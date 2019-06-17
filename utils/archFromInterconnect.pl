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

=item * This is for Aries based systems only. Components are inferred from the network connectivity.

=item * We define (for example) C<c0-0c0s0a0n0> to refer to the NIC and it is a child of the router.

=back

=head1 SEE ALSO

=cut


use strict;

my $nnic_aries = 4;
# from the slots, can infer all, cabs, chassis, nodes, aries. Slot->aries is known
# use hash, so duplicates are automatically handled, even though this means we have increased storage
my %HoHcabinet; #for each cab, hash of chassis
my %HoHchassis; # for each chassis, hash of slots
my %HoHslot; # infer the nodes and the aries
# TODO: rename so can handle gemini.
my %HoHaries; # for each aries, the rc will have tiles and NICs.
my %HoHlink; # for each link --  e1, e2, type. name of the link will be name of the tile. includes ptile links
my %HoHPcieLink; # between node and NIC
my %HoHendpoint; #for each link endpoint, which it its link? nodes, nice, and tiles all go in here

#c0-0c0s0a0l00(0:0:0) green -> c0-0c0s6a0l10(0:0:6)
#c0-0c0s0a0l01(0:0:0) blue -> unused
#c0-0c0s0a0l50(0:0:0) ptile -> processor


sub addLink{
    my ($R0,$E0,$R1,$E1,$lname0,$type) = @_;
    #add this link, otherwise we already have it from the other end
    $HoHlink{$lname0}{'E0'} = $E0;
    $HoHlink{$lname0}{'E1'} = $E1;
    $HoHlink{$lname0}{'R0'} = $R0;
    $HoHlink{$lname0}{'R1'} = $R1;
    $HoHlink{$lname0}{'type'} = $type;
}

sub addEndpoint{
    my ($E0,$type,$lname0,$pcie) = @_;
    $HoHendpoint{$E0}{'type'} = $type;
    $HoHendpoint{$E0}{'link'} = $lname0;
    $HoHendpoint{$E0}{'pcielink'} = $pcie;
}

sub printEndpoint{
    foreach (sort { $b <=> $a } keys(%HoHendpoint) ){
	my $ep = $_;

	if ($HoHendpoint{$ep}{'type'} =~ /TLE/){
	    print ":$ep a craydict:AriesRouterTile ;";
	} elsif ($HoHendpoint{$ep}{'type'} =~ /NIC/){
	    print ":$ep a ddict:NIC ;";
	} elsif ($HoHendpoint{$ep}{'type'} =~ /NDE/){
	    print ":$ep a ddict:ComputeNode ;";
	}

	if (!($HoHendpoint{$ep}{'link'} =~ /N\/A/)){
	    print "\n\tlogset:endPointOf :" . $HoHendpoint{$ep}{'link'} . ";";
	}
	if (!($HoHendpoint{$ep}{'pcielink'} =~ /N\/A/)){
	    print "\n\tlogset:endPointOf :" . $HoHendpoint{$ep}{'pcielink'} . ";";
	}
	print "\t.\n";
    }    
    print "\n";

}

sub addAriesTile{
    my ($R0,$E0) = @_;
    $HoHaries{$R0}{$E0} = "TLE"; #child of the aries
}

sub addAriesNIC{
    my ($R0,$NIC,$nodenum,$lname0) = @_;
    #adding the NIC, adds the node, and the pcielink

    $HoHaries{$R0}{$NIC} = "NIC"; #child of the aries
    #add the node
    if ($R0 =~ /(.*)a0/){
	my $base = $1;
	my $node = $base . "n". $nodenum;
	my $pcie = "pcie" . $node;
	#node is an enpoint
	$HoHPcieLink{$pcie} = 1;
	my @endarr = ();
	addEndpoint($node,"NDE","N/A",$pcie); #endpoint of the pcie
	addEndpoint($NIC,"NIC",$lname0,$pcie); #endpoint of the pcie and the ptile link
    }
}

sub printCabinet{
    foreach (sort { $b <=> $a } keys(%HoHcabinet) ){
	my $cab = $_;
    
	print ":$cab a ddict:Cabinet ;\n";
    print "\trdfs:label \"$cab\" ;\n" ;
	foreach (sort { $b <=> $a } keys %{ $HoHcabinet{$cab} } ){
	    my $chassis = $_;
	    print "\tlogset:hasPart :$chassis ;\n";
	}
	print "\t.\n";
	print "\n";
    }
}


sub printChassis{
    foreach (sort { $b <=> $a } keys(%HoHchassis) ){
	my $chassis = $_;
    
	print ":$chassis a ddict:Chassis ;\n";
    print "\trdfs:label \"$chassis\" ;\n" ;
	foreach (sort { $b <=> $a } keys %{ $HoHchassis{$chassis} } ){
	    my $slot = $_;
	    print "\tlogset:hasPart :$slot;\n";
	}
	print "\t.\n";
	print "\n";
    }
}

sub printSlot{
    foreach (sort { $b <=> $a } keys(%HoHslot) ){
	my $slot = $_;
	print ":$slot a ddict:Blade ;\n";
    print "\trdfs:label \"$slot\" ;\n" ;

	#well known slots have nodes
	for (my $i = 0; $i < 4; $i++){
	    print "\tlogset:hasPart :$slot" . "n$i;\n";
	}

	#well known slots have aries
	print "\tlogset:hasPart :$slot" . "a0;\n";
	print "\t.\n";
	print "\n";
    }
}


sub printAries{
    #aries will have both tile and NIC children. they will be added as endpoints

    foreach (sort { $b <=> $a } keys(%HoHaries) ){
	my $aries = $_;
	print ":$aries a craydict:AriesRouter ;\n";
    print "\trdfs:label \"$aries\" ;\n" ;
	foreach (sort { $b <=> $a } keys %{ $HoHaries{$aries} } ){
	    my $child = $_; # children are both TILES and NICS. Here we do not care which type
	    print "\tlogset:hasPart :$child ;\n";
	}
	print "\t.\n";
	print "\n";
    }
}

sub printPcieLink{
    foreach (sort { $b <=> $a } keys(%HoHPcieLink) ){
	my $link = $_;
	print ":$link a ddict:pcieLink .\n";
    }
    print "\n";
}
    

sub printLink{
    foreach (sort { $b <=> $a } keys(%HoHlink) ){
	my $link = $_;

	if ($HoHlink{$link}{'type'} =~ /BLU/){
	    print ":$link a craydict:BlueLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /GRE/){
	    print ":$link a craydict:GreenLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /BLK/){
	    print ":$link a craydict:BlackLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /PTL/){
	    print ":$link a craydict:Ptile .\n";
	}
    }
    print "\n";
}

sub printPrefixes{
    print "\@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n";
    print "\@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n";
    print "\@prefix adms: <http://www.w3.org/ns/adms#> .\n";
    print "\@prefix dct: <http://purl.org/dc/terms/> .\n";
    print "\@prefix logset: <http://portal.nersc.gov/project/mpccc/sleak/resilience/datasets/logset#> .\n";
    print "\@prefix ddict: <http://portal.nersc.gov/project/mpccc/sleak/resilience/datasets/ddict#> .\n";
    print "\@base <file:///global/homes/s/sleak/Monitoring/Resilience/LogSet/examples/> .\n";
    print "\@prefix craydict: <cray-dict#> .\n";
    print "\n";
    print "# declare myself and set a prefix:\n";
    #print "\@base <http://FIXME/where/will/this/be/published> .\n";
    print "\@base <file:///global/homes/s/sleak/Monitoring/Resilience/LogSet/examples/> .\n";
    print "\@prefix : <edison-arch#> .\n";
    print "\n";
    print ":\n";
    print "\ta adms:Asset ;\n";
    print "\tdct:title \"FIXME give this file a title\" ;\n";
    print "\trdfs:label \"FIXME short label\" ;\n";
    print "\t.\n";
    print "\n";
}

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

	#what type of connection is this?
	my $type = -1;
	if ($vals[1] eq 'blue'){
	    $type = "BLU";
	} elsif ($vals[1] eq 'black'){
	    $type = "BLK";
	} elsif ($vals[1] eq 'green'){
	    $type = "GRE";
	} elsif ($vals[1] eq 'ptile'){
	    $type = "PTL";
	} elsif ($vals[1] eq 'host'){ # DNE
	    $type = "HST";
	} else {
	    $type = "UNK";
	}

	#first entry should always be a valid tile
	if (($vals[0] =~ /(.*)\[/) || ($vals[0] =~ /(.*\d)\(/)){
	    $E0 = $1;
	    if ($E0 =~ /(.*)l/){
		$R0 = $1;
		addAriesTile($R0,$E0);
	    }
	}

	if (($vals[3] =~ /(.*)\[/) || ($vals[3] =~ /(.*\d)\(/)){
	    # this is a 2-ended link
	    $E1 = $1;
	    if ($E1 =~ /(.*)l/){
		$R1 = $1;
		#dont add the aries for this side; will pick it up on the other side of the link
	    }

	    # these will readin as double, one for each endpoint, so check to see if we already have this one
	    my $lname0 = "link" . $E0;
	    my $lname1 = "link" . $E1;
	    if (!(exists $HoHlink{$lname0}) && !(exists $HoHlink{$lname1})){
		#add this link, otherwise we already have it from the other end
		addEndpoint($E0,"TLE",$lname0,"N/A");
		addEndpoint($E1,"TLE",$lname0,"N/A");
		addLink($R0,$E0,$R1,$E1,$lname0,$type);
	    }
	} elsif ($vals[3] =~ /unused/){
	    #$E1 = "unused"; does not matter
	    #$R1 = "unused"; does not matter
	    #add the tile, but not the link
	    addAriesTile($R0,$E0);
	    addEndpoint($E0,"TLE","N/A","N/A");
	} elsif ($vals[3] =~ /processor/){
	    # TODO: Gemini
	    # This endpoint is a NIC. aries has 4 NIC and 8 ptiles, in order. get the last digit
	    my $node = -1;
	    if ($E0 =~ /.*(\d)/){
		my $lname0 = "link" . $E0;
		$R1 = $R0;
		my $lastdigit = $1;
		if ($lastdigit < 2){
		    $node = 0;
		} elsif ($lastdigit < 4){
		    $node = 1;
		} elsif ($lastdigit < 6){
		    $node = 2;
		} elsif ($lastdigit < 8){
		    $node = 3;
		} else {
		    die "Cannot determine NIC for $E0\n";
		}

		$E1 = $R0 . "n". $node;
		addAriesTile($R0,$E0);
		addEndpoint($E0,"TLE",$lname0,"N/A");
		addLink($R0,$E0,$R1,$E1,$lname0,$type); #add the ptile link
		addAriesNIC($R1,$E1,$node,$lname0); #add the NIC, NODE, and pcie link
	    }
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
    }
} # while

printPrefixes();
printCabinet();
printChassis();
printSlot();
printAries();
printLink();
printEndpoint();
printPcieLink();


