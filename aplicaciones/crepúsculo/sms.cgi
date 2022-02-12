1#!/usr/bin/perl

2# $Id: sms.cgi,v 1.1 2012-04-09 16:12:17 ericblue76 Exp $
3#
4# Author: Eric Blue - http://eric-blue.com
5# Project: STEM - Samsung TV Enhanced Messaging
6# Description:  Sends SMS messages to your Samsung TV using Twilio (http://www.twilio.com/)
7#
8#

9use CGI;
10use CGI::Carp qw/fatalsToBrowser/;
11use LWP::UserAgent;
12use HTTP::Request;
13use XML::Simple;
14use HTML::Entities;
15use POSIX;
16use Carp;
17use strict;

18# TODO Add time of day settings to only send notifications in the evenings and on weekends

19sub load_config {

 20   my ($filename) = @_;

   21 $/ = "";
 22   open( CONFIG, "$filename" ) or croak "Can't open config $filename!";
 23   my $config_file = <CONFIG>;
  24  close(CONFIG);
   25 undef $/;

  26  my $config = eval($config_file) or croak "Invalid config file format!";

 27   return $config;

28}

29# Load config, or just define them inline
30my $config = load_config("stem.cnf");

31print "Content-type: text/xml\n\n";

32# Have Twilio forward to your normal number while the notification to your TV happens
33print qq{<?xml version="1.0" encoding="UTF-8"?>};

34print qq{ 
35<Response> 
 36   <Sms>Message Recieved</Sms>
37</Response>
38};

39my $cgi = CGI->new();

40my $from_phone = $cgi->param('From');
41$from_phone = "Unknown" if !defined($from_phone);

42my $body = $cgi->param('Body');

43my $from_city = $cgi->param('FromCity');
44$from_phone = "Unknown City" if !defined($from_city);

45my $from_state = $cgi->param('FromState');
46$from_state = "Unknown State" if !defined($from_state);


47my $sms = {
48	Category    => 'SMS',
49	DisplayType => 'Maximum',
50	ReceiveTime    => {
51		Date => strftime( "%Y-%m-%d", localtime),
52		Time => strftime( "%H:%M:%S", localtime)
53	},
54	Receiver => {
55		Name   => 'Me',
56		Number => $config->{'forward_phone'}
57	},
58	Sender => {
59		Name   => "$from_city, $from_state",
60		Number => $from_phone
61	},
62	Body => $body
63};

64my $sms_xml = XMLout( $sms, RootName => undef, NoAttr => 1 );
65my $sms_xml_encoded = encode_entities($sms_xml);
66chop $sms_xml_encoded;

67# Load the template SOAP body and insert the encoded XML message

68open( TEMPLATE, "template/soap_envelope.tpl" )
69  or die "Can't open SOAP envelope!";
70my $soap_envelope = do { local ($/); <TEMPLATE> };
71close(TEMPLATE);

72my $message = $soap_envelope;
73$message =~ s/\$MESSAGE\$/$sms_xml_encoded/;

74# Send the call notification to the TV

75my $userAgent = LWP::UserAgent->new();
76my $request   =
77  HTTP::Request->new(
78	POST => "http://$config->{'tvip'}:52235/PMR/control/MessageBoxService" );
79$request->header(
80	SOAPAction => '"urn:samsung.com:service:MessageBoxService:1#AddMessage"' );
81$request->content($message);
82$request->content_type("text/xml; charset=utf-8");

83my $response = $userAgent->request($request);

84if($response->code != 200) {
85	warn $response->error_as_HTML;
86}

