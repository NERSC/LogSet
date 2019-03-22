#!/usr/bin/perl

=pod

=head1 NAME

archFromInterconnect.pl

=head1 SYNOPSIS

cat rtrfile.txt | ./archFromInterconnect.pl > arch.out


=head1 DESCRIPTION

For Cray systems, this builds the properties of the commponents based on the output
of rtr --interconnect

=head1 NOTES

=over

=item * This is for Cray Gemini and Aries based systems only. Components are inferred from the network connectivity.

=item * We define (for example) C<c0-0c0s0a0n0> to refer to the NIC and it is a child of the router.

=back

=head1 SEE ALSO

=cut


use strict;

# from the slots, can infer all, cabs, chassis, nodes, aries. Slot->aries is known
my %HoHcabinet; #for each cab, hash of chassis
my %HoHchassis; # for each chassis, hash of slots
my %HoHslot; #infer the nodes and the aries
my %HoHaries; # for each aries, the rc will have tiles
my %HoHlink; #for each link --  e1, e2, type. name of the link will be name of the tile
my %endpoint; #for each endpoint, which it its link?

#c0-0c0s0a0l00(0:0:0) green -> c0-0c0s6a0l10(0:0:6)
#c0-0c0s0a0l01(0:0:0) blue -> unused
#c0-0c0s0a0l50(0:0:0) ptile -> processor

while(<>){
    chomp;
    my $line = $_;
    $line =~ tr/-/_/; # WARNING: will need to do underscore in all the matching...

    if ($line =~ /\_>/){
	my @vals = split(/\s+/,$line);
	if (scalar(@vals) != 4){
	    die "Bad line: <$line>\n";
	}
	my $E0 = -1;
	my $E1 = -1;
	my $R0 = -1;
	my $R1 = -1;

	if (($vals[0] =~ /(.*)\[/) || ($vals[0] =~ /(.*\d)\(/)){
	    $E0 = $1;
	    if ($E0 =~ /(.*)l/){
		$R0 = $1;
		$HoHaries{$R0}{$E0} = 1;
	    }
	}

	my $type = -1;
	if ($vals[1] eq 'X+'){
	    $type = "XP0";
	} elsif ($vals[1] eq 'X_'){
	    $type = "XM0";
	} elsif ($vals[1] eq 'Y+'){
	    $type = "YP0";
	} elsif ($vals[1] eq 'Y_'){
	    $type = "YM0";
	} elsif ($vals[1] eq 'Z+'){
	    $type = "ZP0";
	} elsif ($vals[1] eq 'Z_'){
	    $type = "ZM0";
	} elsif ($vals[1] eq 'blue'){
	    $type = "BLU";
	} elsif ($vals[1] eq 'black'){
	    $type = "BLK";
	} elsif ($vals[1] eq 'green'){
	    $type = "GRE";
	} elsif ($vals[1] eq 'ptile'){
	    $type = "PTL";
	} elsif ($vals[1] eq 'host'){
	    $type = "HST";
	} else {
	    $type = "UNK";
	}

	if (($vals[3] =~ /(.*)\[/) || ($vals[3] =~ /(.*\d)\(/)){
	    $E1 = $1;
	    if ($E1 =~ /(.*)l/){
		$R1 = $1;
#		$HoHaries{$R1}{$E1} = 1; dont need this since will pick it up on the other side
	    }

	    # these will readin as double, one for each endpoint, so check to see if we already have this one
	    my $lname0 = "link" . $E0;
	    my $lname1 = "link" . $E1;
	    if (!(exists $HoHlink{$lname0}) && !(exists $HoHlink{$lname1})){
		#add this link, otherwise we already have the other end
		$HoHlink{$lname0}{'E0'} = $E0;
		$HoHlink{$lname0}{'E1'} = $E1;
		$HoHlink{$lname0}{'R0'} = $R0;
		$HoHlink{$lname0}{'R1'} = $R1;
		$HoHlink{$lname0}{'type'} = $type;
		$endpoint{$E0} = $lname0;
		$endpoint{$E1} = $lname0;
	    }
	} elsif ($vals[3] =~ /unused/){
	    #type is still correct for this tile
	    $E1 = 'unused';
	    $R1 = 'unused';
	} elsif ($vals[3] =~ /processor/){
	    #type is still correct for this tile
	    $E1 = 'processor';
	    $R1 = 'processor';
	    #add this link 
	    my $lname0 = "link" . $E0;
	    $HoHlink{$lname0}{'E0'} = $E0;
	    $HoHlink{$lname0}{'E1'} = $E1;
	    $HoHlink{$lname0}{'R0'} = $R0;
	    $HoHlink{$lname0}{'R1'} = $R1;
	    $HoHlink{$lname0}{'type'} = $type;
	    $endpoint{$E0} = $lname0;
	    #TODO...this endpoint is the NIC
	}


	# add the cab, chassis, slot if exist
	if ($R1 =~ /(c\d+_\d+)/){
	    my $cab = $1;
	    if ($R1 =~ /(c\d+_\d+c\d+)/){
		my $chassis = $1;
		$HoHcabinet{$cab}{$chassis} = 1;
		my $slot = -1;
		if ($R1 =~ /(c\d+_\d+c\d+s\d+)/){
		    $slot = $1;
		}
		$HoHchassis{$chassis}{$slot} = 1;
		$HoHslot{$slot} = 1;
	    }
	}

#	    #the other direction should be in there in the case of a network link
#	    #for non-link (e.g., ptile or unused)......
#	}

    }
}

# ALL THE WRITEOUTS ARE HERE
    
foreach (sort { $b <=> $a } keys(%HoHcabinet) ){
    my $cab = $_;
    
#    print "$cab is a cabinet with chassis:\n";
    print ":$cab a ddict:cabinet\n";
    foreach (sort { $b <=> $a } keys %{ $HoHcabinet{$cab} } ){
	my $chassis = $_;
#	print "\t$chassis\n";
	print "\tlogset:hasPart :$chassis;\n";
    }
    print "\t.\n";
    print "\n";
}


foreach (sort { $b <=> $a } keys(%HoHchassis) ){
    my $chassis = $_;
    
#    print "$chassis is a chassis with slots:\n";
    print ":$chassis a ddict:chassis\n";
    foreach (sort { $b <=> $a } keys %{ $HoHchassis{$chassis} } ){
	my $slot = $_;
	print "\tlogset:hasPart :$slot;\n";
    }
    print "\t.\n";
    print "\n";
}

foreach (sort { $b <=> $a } keys(%HoHslot) ){
    my $slot = $_;
#    print "$slot is a slot with well known:\n";
    print ":$slot a ddict:blade\n";
    for (my $i = 0; $i < 4; $i++){
#	print "\t" . $slot . "n$i\n";
	print "\tlogset:hasPart :$slot" . "n$i;\n";
    }
#    print "\t" . $slot . "a0\n";
    print "\tlogset:hasPart :$slot" . "a0;\n";
    print "\t.\n";
    print "\n";
}


foreach (sort { $b <=> $a } keys(%HoHaries) ){
    my $aries = $_;
#    print "$aries is a aries with tiles;\n";
    print ":$aries a cray-dict:ariesRouter\n";
    foreach (sort { $b <=> $a } keys %{ $HoHaries{$aries} } ){
	my $tile = $_;
#	print "\t$tile\n";
	print "\tlogset:hasPart :$tile;\n";
    }
    print "\t.\n";
    print "\n";
}



foreach (sort { $b <=> $a } keys(%HoHlink) ){
    my $link = $_;

#    print "<$link> is a link with endpoints and type: \n";
#    print "\t" . $HoHlink{$link}{'E0'} . "\n";
#    print "\t" . $HoHlink{$link}{'E1'}. "\n";
#    print "\t" . $HoHlink{$link}{'type'}. "\n";
    if ($HoHlink{$link}{'type'} =~ /BLU/){
	print ":$link a cray-dict:blueLink .\n";
    }
    if ($HoHlink{$link}{'type'} =~ /GRE/){
	print ":$link a cray-dict:greenLink .\n";
    }
    if ($HoHlink{$link}{'type'} =~ /BLK/){
	print ":$link a cray-dict:blackLink .\n";

    }
    #skipping ptiles for now
}
print "\n";

foreach (sort { $b <=> $a } keys(%endpoint) ){
    my $xendpoint = $_;
#    print "<$endpoint> is an endpoint of link :\n"; 
    print ":$xendpoint a cray-dict:ariesRouterTile\n";
#    print "\t" . $endpoint{$endpoint}. "\n";
    print "\tlogset:endPointOf :" . $endpoint{$xendpoint} . ";\n";
    print "\t.\n";
    print "\n";
}

