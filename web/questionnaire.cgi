#!/usr/bin/perl -w -I../perllib

# questionnaire.cgi:
# Questionnaire for problem creators
#
# Copyright (c) 2007 UK Citizens Online Democracy. All rights reserved.
# Email: matthew@mysociety.org. WWW: http://www.mysociety.org
#
# $Id: questionnaire.cgi,v 1.17 2007-08-29 23:03:16 matthew Exp $

use strict;
use Standard;
use Error qw(:try);
use CrossSell;
use mySociety::AuthToken;
use mySociety::MaPit;
use mySociety::Web qw(ent);


sub main {
    my $q = shift;
    my $out = '';
    if ($q->param('submit')) {
        $out = submit_questionnaire($q);
    } else {
        $out = display_questionnaire($q);
    }
    print Page::header($q, title=>_('Questionnaire'));
    print $out;
    print Page::footer();
}
Page::do_fastcgi(\&main);

sub check_stuff {
    my $q = shift;

    my $id = mySociety::AuthToken::retrieve('questionnaire', $q->param('token'));
    throw Error::Simple("I'm afraid we couldn't validate that token. If you've copied the URL from an email, please check that you copied it exactly.\n") unless $id;

    my $questionnaire = dbh()->selectrow_hashref(
        'select id, problem_id, whenanswered from questionnaire where id=?', {}, $id);
    my $problem_id = $questionnaire->{problem_id};
    throw Error::Simple("You have already answered this questionnaire. If you have a question, please <a href=/contact>get in touch</a>, or <a href=/?id=$problem_id>view your problem</a>.\n") if $questionnaire->{whenanswered};

    my $prev_questionnaire = dbh()->selectrow_hashref(
        'select id from questionnaire where problem_id=? and whenanswered is not null', {}, $problem_id);

    my $problem = dbh()->selectrow_hashref(
        "select *, extract(epoch from confirmed) as time, extract(epoch from whensent-confirmed) as whensent
            from problem where id=? and state in ('confirmed','fixed')", {}, $problem_id);
    throw Error::Simple("I'm afraid we couldn't locate your problem in the database.\n") unless $problem;

    return ($questionnaire, $prev_questionnaire, $problem);
}

sub submit_questionnaire {
    my $q = shift;
    my @vars = qw(token id been_fixed reported update another);
    my %input = map { $_ => scalar $q->param($_) || '' } @vars;
    my %input_h = map { $_ => $q->param($_) ? ent($q->param($_)) : '' } @vars;
 
    my ($error, $questionnaire, $prev_questionnaire, $problem);
    try {
        ($questionnaire, $prev_questionnaire, $problem) = check_stuff($q);
    } catch Error::Simple with {
        my $e = shift;
        $error = $e;
    };
    return $error if $error;

    my @errors;
    push @errors, 'Please state whether or not the problem has been fixed' unless $input{been_fixed};
    push @errors, 'Please say whether you\'ve ever reported a problem to your council before' unless $input{reported} || $prev_questionnaire;
    push @errors, 'Please indicate whether you\'d like to receive another questionnaire'
        if $input{been_fixed} eq 'No' && !$input{another};
    push @errors, 'Please provide some explanation as to why you\'re reopening this report'
        if $input{been_fixed} eq 'No' && $problem->{state} eq 'fixed' && !$input{update};
    return display_questionnaire($q, @errors) if @errors;

    my $new_state = '';
    $new_state = 'fixed' if $input{been_fixed} eq 'Yes' && $problem->{state} eq 'confirmed';
    $new_state = 'confirmed' if $input{been_fixed} eq 'No' && $problem->{state} eq 'fixed';

    # Record state change, if there was one
    dbh()->do("update problem set state=?, lastupdate=ms_current_timestamp()
        where id=?", {}, $new_state, $problem->{id})
        if $new_state;

    # If it's not fixed and they say it's still not been fixed, record time update
    dbh()->do("update problem set lastupdate=ms_current_timestamp()
        where id=?", {}, $problem->{id})
        if $input{been_fixed} eq 'No' && $problem->{state} eq 'confirmed';

    # Record questionnaire response
    my $reported = $input{reported}
        ? ($input{reported} eq 'Yes' ? 't' : ($input{reported} eq 'No' ? 'f' : undef))
        : undef;
    dbh()->do('update questionnaire set whenanswered=ms_current_timestamp(),
        ever_reported=?, old_state=?, new_state=? where id=?', {},
        $reported, $problem->{state}, $new_state ? $new_state : $problem->{state},
        $questionnaire->{id});

    # Record an update if they've given one, or if there's a state change
    my $name = $problem->{anonymous} ? undef : $problem->{name};
    my $update = $input{update} ? $input{update} : 'Questionnaire filled in by problem reporter';
    dbh()->do("insert into comment
        (problem_id, name, email, website, text, state, mark_fixed, mark_open)
        values (?, ?, ?, ?, ?, 'confirmed', ?, ?)", {},
        $problem->{id}, $name, $problem->{email}, '', $update,
        $new_state eq 'fixed' ? 't' : 'f', $new_state eq 'confirmed' ? 't' : 'f'
    )
        if $new_state || $input{update};

    # If they've said they want another questionnaire, mark as such
    dbh()->do("update problem set send_questionnaire = 't' where id=?", {}, $problem->{id})
        if $input{been_fixed} eq 'No' && $input{another} eq 'Yes';

    dbh()->commit();
    if ($new_state eq 'confirmed' || (!$new_state && $problem->{state} eq 'confirmed')) {
        return <<EOF;
<p style="font-size:200%">We're sorry to hear that. We have two suggestions: why not try
<a href="http://www.writetothem.com/">writing direct to your councillor(s)</a>
or, if it's a problem that could be fixed by local people working together,
why not <a href="http://www.pledgebank.com/new">make and publicise a pledge</a>?
</p>
EOF
    } else {
        my $out = <<EOF;
<p>Thank you very much for filling in our questionnaire; glad to hear it's been fixed.</p>
EOF
        $out .= CrossSell::display_advert($problem->{email}, $problem->{name});
    }
}

sub display_questionnaire {
    my ($q, @errors) = @_;
    my @vars = qw(token id been_fixed reported update another);
    my %input = map { $_ => $q->param($_) || '' } @vars;
    my %input_h = map { $_ => $q->param($_) ? ent($q->param($_)) : '' } @vars;

    my ($error, $questionnaire, $prev_questionnaire, $problem);
    try {
        ($questionnaire, $prev_questionnaire, $problem) = check_stuff($q);
    } catch Error::Simple with {
        my $e = shift;
        $error = $e;
    };
    return $error if $error;

    my $x = Page::os_to_tile($problem->{easting});
    my $y = Page::os_to_tile($problem->{northing});
    my $x_tile = int($x);
    my $y_tile = int($y);
    my $px = Page::os_to_px($problem->{easting}, $x_tile);
    my $py = Page::os_to_px($problem->{northing}, $y_tile);

    my $pins = Page::display_pin($q, $px, $py, $problem->{state} eq 'fixed'?'green':'red');
    my $problem_text = Page::display_problem_text($q, $problem);
    my $updates = Page::display_problem_updates($problem->{id});
    my $out = '';
    $out .= Page::display_map($q, x => $x_tile, y => $y_tile, pins => $pins,
        px => $px, py => $py, pre => $problem_text, post => $updates );
    my %been_fixed = (
        yes => $input{been_fixed} eq 'Yes' ? ' checked' : '',
        no => $input{been_fixed} eq 'No' ? ' checked' : '',
    );
    my %reported = (
        yes => $input{reported} eq 'Yes' ? ' checked' : '',
        no => $input{reported} eq 'No' ? ' checked' : '', 
    );
    my %another = (
        yes => $input{another} eq 'Yes' ? ' checked' : '',
        no => $input{another} eq 'No' ? ' checked' : '', 
    );
    $out .= <<EOF;
<h1>Questionnaire</h1>
<form method="post" action="/questionnaire" id="questionnaire">
<input type="hidden" name="token" value="$input_h{token}">

<p>The details of your problem are available on the right hand side of this page.
EOF
    $out .= 'Please take a look at the updates that have been left.' if $updates;
    $out .= '</p>';
    if (@errors) {
        $out .= '<ul id="error"><li>' . join('</li><li>', @errors) . '</li></ul>';
    }
    $out .= '<p>';
    $out .= 'An update marked this problem as fixed. ' if $problem->{state} eq 'fixed';
    $out .= 'Has the problem been fixed?</p>';
    $out .= <<EOF;
<p align="center">
<input type="radio" name="been_fixed" id="been_fixed_yes" value="Yes"$been_fixed{yes}>
<label for="been_fixed_yes">Yes</label>
<input type="radio" name="been_fixed" id="been_fixed_no" value="No"$been_fixed{no}>
<label for="been_fixed_no">No</label>
</p>
EOF
    $out .= <<EOF unless $prev_questionnaire;
<p>Have you ever reported a problem to a council before?</p>
<p align="center">
<input type="radio" name="reported" id="reported_yes" value="Yes"$reported{yes}>
<label for="reported_yes">Yes</label>
<input type="radio" name="reported" id="reported_no" value="No"$reported{no}>
<label for="reported_no">No</label>
</p>
EOF
    $out .= <<EOF;
<p>If you wish to leave a public update on the problem, please enter it here
(please note it will not be sent to the council). For example, what was
your experience of getting the problem fixed?</p>
<p><textarea name="update" style="width:90%" rows="7" cols="30">$input_h{update}</textarea></p>

<div id="another_qn">
<p>Would you like to receive another questionnaire in 4 weeks, reminding you to check the status?</p>
<p align="center">
<input type="radio" name="another" id="another_yes" value="Yes"$another{yes}>
<label for="another_yes">Yes</label>
<input type="radio" name="another" id="another_no" value="No"$another{no}>
<label for="another_no">No</label>
</p>
</div>

<p align="right"><input type="submit" name="submit" value="Submit questionnaire"></p>
</form>
EOF
    $out .= Page::display_map_end(0);
    return $out;
}
