//
//  EditSubjectViewController.m
//  FixMyStreet
//
//  Created by Matthew on 01/10/2008.
//  Copyright 2008 UK Citizens Online Democracy. All rights reserved.
//

#import "EditSubjectViewController.h"
#import "EditingTableViewCell.h"
#import "FixMyStreetAppDelegate.h"

@implementation EditSubjectViewController

@synthesize cell;

/*
- (id)initWithStyle:(UITableViewStyle)style {
    // Override initWithStyle: if you create the controller programmatically and want to perform customization that is not appropriate for viewDidLoad.
    if (self = [super initWithStyle:style]) {
    }
    return self;
}
*/

-(void)setAll:(NSString*)a viewTitle:(NSString*)b placeholder:(NSString*)c keyboardType:(UIKeyboardType)d capitalisation:(UITextAutocapitalizationType)e {
	cell = [[EditingTableViewCell alloc] initWithFrame:CGRectZero reuseIdentifier:@"EditingCell"];
	cell.textField.delegate = self;
	cell.textField.placeholder = c;
	self.title = b;
	if (a) cell.textField.text = a;
	cell.textField.keyboardType = d;
	if (b == @"Edit name" || b == @"Edit email") {
		cell.textField.autocorrectionType = UITextAutocorrectionTypeNo;
	}
	cell.textField.autocapitalizationType = e;
}

// Implement viewDidLoad to do additional setup after loading the view.
- (void)viewDidLoad {
    [super viewDidLoad];
	self.tableView.sectionHeaderHeight = 27.0;
	self.tableView.sectionFooterHeight = 0.0;
//	self.title = viewTitle;
}

- (NSInteger)numberOfSectionsInTableView:(UITableView *)tableView {
	if (cell.textField.placeholder == @"Subject") {
		return 2;
	}
    return 1;
}


- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section {
    return 1;
}

- (CGFloat)tableView:(UITableView *)tableView heightForRowAtIndexPath:(NSIndexPath *)indexPath {
	if (indexPath.section == 1) {
		return 54.0;
	}
	return 44.0;
}

- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)indexPath {
	if (indexPath.section == 1) {
		static NSString *CellIdentifier = @"InfoCell";
		UITableViewCell *infoCell = [tableView dequeueReusableCellWithIdentifier:CellIdentifier];
		if (infoCell == nil) {
			infoCell = [[[UITableViewCell alloc] initWithFrame:CGRectZero reuseIdentifier:CellIdentifier] autorelease];
			UITextView *blurb = [[UITextView alloc] initWithFrame:CGRectMake(10, 0, 280, 44)];
			blurb.font = [UIFont italicSystemFontOfSize:14];
			blurb.textAlignment = UITextAlignmentCenter;
			blurb.editable = NO;
			blurb.text = @"You can provide more details\nlater on at the website";
			[infoCell.contentView addSubview:blurb];
			[blurb release];
		}
		return infoCell;
	}

	return cell;
}

- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)indexPath {
	[tableView deselectRowAtIndexPath:indexPath animated:NO];
	[cell.textField becomeFirstResponder];
}

- (void)viewWillAppear:(BOOL)animated {
    //[super viewWillAppear:animated];
	[cell.textField becomeFirstResponder];
}

/*
- (void)viewDidAppear:(BOOL)animated {
    [super viewDidAppear:animated];
}
*/

- (void)viewWillDisappear:(BOOL)animated {
	// On 2.0 this produces same effect as clicking Done, but not in 2.1?
	[cell.textField resignFirstResponder];
}

/*
- (void)viewDidDisappear:(BOOL)animated {
}
*/
/*
- (void)didReceiveMemoryWarning {
    [super didReceiveMemoryWarning];
}
*/

- (void)dealloc {
	[cell release];
    [super dealloc];
}


-(void)updateText:(NSString*)text {
	FixMyStreetAppDelegate *delegate = [[UIApplication sharedApplication] delegate];
	// This is yucky, but I can't think of a better way that wouldn't just waste time.
	NSString* placeholder = cell.textField.placeholder;
	if (placeholder == @"Subject") {
		if (text.length) {
			delegate.subject = text;
		} else {
			delegate.subject = nil;
		}
	} else if (placeholder == @"Your name") {
		if (text.length) {
			delegate.name = text;
		} else {
			delegate.name = nil;
		}
	} else if (placeholder == @"Your email") {
		if (text.length) {
			delegate.email = text;
		} else {
			delegate.email = nil;
		}
	} else if (placeholder == @"Your phone number") {
		if (text.length) {
			delegate.phone = text;
		} else {
			delegate.phone = nil;
		}
	}
	[self.navigationController popViewControllerAnimated:YES];
}

-(BOOL)textFieldShouldReturn:(UITextField*)theTextField {
	//if (theTextField == subjectTextField) {
	[theTextField resignFirstResponder];
	[self updateText:theTextField.text];
	//}
	return YES;
}

@end

