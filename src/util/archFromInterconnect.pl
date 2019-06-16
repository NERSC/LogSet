#!/usr/bin/perl

=pod

=head1 NAME

archFromInterconnect.pl

=head1 SYNOPSIS

./archFromInterconnect.pl --rtrfile=rtr.out --arch=XC > arch.out


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

# WARNING: In process of editing for gemini. 
# Issues:
# * gemini service dont have same number of nodes as compute. (Do we need to know about service and compute in aries?)
# * will need to infer the processor facing tiles (l23, l24, l33, l34, l43, l44, l53, l54). Can't recall ptile <-> NIC
# * torus links are directional, whereas XC links are not. We drop direction here.

use strict;
use Getopt::Long;

my $fh;
my $nnic_aries = 4;
my $nnodeperslot_aries = 4;
# from the slots, can infer all, cabs, chassis, nodes, aries. Slot->aries is known
# use hash, so duplicates are automatically handled, even though this means we have increased storage
my %HoHcabinet; #for each cab, hash of chassis
my %HoHchassis; # for each chassis, hash of slots
my %HoHslot; # for each slot, infer the nodes and the rtrs
my %HoHaries; # for each aries, tiles and NICs (value is type)
my %HoHlink; # for each link --  e1, e2, type. name of the link will be name of the tile. includes ptile links
my %HoHPcieLink; # between node and NIC
my %HoHendpoint; #for each link endpoint, which it its link? nodes, NICs, and tiles all go in here
#NICs are endpoints of links (from tile) and pcielinks (to node)

#c0-0c0s0a0l00(0:0:0) green -> c0-0c0s6a0l10(0:0:6)
#c0-0c0s0a0l01(0:0:0) blue -> unused
#c0-0c0s0a0l50(0:0:0) ptile -> processor

my $arch='';
my $rtrfile='';

GetOptions("arch=s" => \$arch,
           "rtrfile=s" => \$rtrfile)
or die "Error in command line arguments\n";

if (!($arch eq "XC")){ # && !($arch eq "XE")){
    die "Only XC supported\n";
}

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
    #only the NIC is an endpoint of both a link and a pcielink
}

sub printEndpoint{
    foreach (sort { $a <=> $b || $a cmp $b } keys(%HoHendpoint) ){
	my $ep = $_;

	if ($HoHendpoint{$ep}{'type'} =~ /TLE/){
	    print ":$ep a cray-dict:ariesRouterTile";
	} elsif ($HoHendpoint{$ep}{'type'} =~ /NIC/){
	    print ":$ep a ddict:nic";
	} elsif ($HoHendpoint{$ep}{'type'} =~ /NDE/){
	    print ":$ep a ddict:computeNode";
	}

	# only NIC is endpoint of both
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

sub addTile{
    my ($R0,$E0,$arch) = @_;
    if ($arch =~ /XC/){
	$HoHaries{$R0}{$E0} = "TLE"; #child of the aries
#    } else {
#	$HoHgemini{$R0}{$E0} = "TLE"; #child of the gemini DNE yet.....
    }
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
    foreach my $cab (sort { $a <=> $b || $a cmp $b } keys(%HoHcabinet) ){
	print ":$cab a ddict:cabinet\n";
	foreach my $chassis (sort { $a <=> $b || $a cmp $b } keys %{ $HoHcabinet{$cab} } ){
	    print "\tlogset:hasPart :$chassis;\n";
	}
	print "\t.\n";
	print "\n";
    }
}


sub printChassis{
    foreach (sort { $a <=> $b || $a cmp $b } keys(%HoHchassis) ){
	my $chassis = $_;
    
	print ":$chassis a ddict:chassis\n";
	foreach (sort { $a <=> $b || $a cmp $b } keys %{ $HoHchassis{$chassis} } ){
	    my $slot = $_;
	    print "\tlogset:hasPart :$slot;\n";
	}
	print "\t.\n";
	print "\n";
    }
}

sub printAriesSlot{

    my $nnodes = 0;
    my $rtrtype  = '';
    my $nnodes = $nnodeperslot_aries;

    foreach (sort { $a <=> $b || $a cmp $b } keys(%HoHslot) ){
	my $slot = $_;
	print ":$slot a ddict:blade\n";

	#well known slots have nodes
	for (my $i = 0; $i < $nnodes; $i++){
	    print "\tlogset:hasPart :$slot" . "n$i;\n";
	}

	#well known slots have routers
	print "\tlogset:hasPart :$slot" . "a0;\n";
	print "\t.\n";
	print "\n";
    }
}


sub printAries{
    #aries will have both tile and NIC children. they will be added as endpoints

    foreach (sort { $a <=> $b || $a cmp $b } keys(%HoHaries) ){
	my $aries = $_;
	print ":$aries a cray-dict:ariesRouter\n";
	foreach (sort { $a <=> $b || $a cmp $b } keys %{ $HoHaries{$aries} } ){
	    my $child = $_; # children are both TILES and NICS. Here we do not care which type
	    print "\tlogset:hasPart :$child;\n";
	}
	print "\t.\n";
	print "\n";
    }
}

sub printPcieLink{
    foreach (sort { $a <=> $b || $a cmp $b } keys(%HoHPcieLink) ){
	my $link = $_;
	print ":$link a ddict:pcieLink .\n";
    }
    print "\n";
}
    

sub printLink{
    foreach (sort { $a <=> $b || $a cmp $b } keys(%HoHlink) ){
	my $link = $_;

	if ($HoHlink{$link}{'type'} =~ /BLU/){
	    print ":$link a cray-dict:blueLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /GRE/){
	    print ":$link a cray-dict:greenLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /BLK/){
	    print ":$link a cray-dict:blackLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /PTL/){
	    print ":$link a cray-dict:ptileLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /Xp/){
	    print ":$link a cray-dict:XpLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /Xm/){
	    print ":$link a cray-dict:XmLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /Yp/){
	    print ":$link a cray-dict:YpLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /Ym/){
	    print ":$link a cray-dict:YmLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /Zp/){
	    print ":$link a cray-dict:ZpLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /Zm/){
	    print ":$link a cray-dict:ZmLink .\n";
	}
    }
    print "\n";
}


open(my $fh, "<", $rtrfile)
    or die "Can't open rtrfile: $!";

while(<$fh>){
    chomp;
    my $line = $_;
    $line =~ tr/-/_/; # WARNING: will need to do underscore in all the matching...

    if ($line =~ /\_>/){
	my @vals = split(/\s+/,$line);
	if (($arch eq "XC" && (scalar(@vals) != 4)) ||
	    ($arch eq "XE" && (scalar(@vals) != 6))){
	    die "Bad line <$line>\n";
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
	} elsif ($vals[1] eq 'ptile'){ # ptile only in the aries rtr output
	    $type = "PTL";
	} elsif ($vals[1] eq 'host'){ # DNE
	    $type = "HST";
#NOTE: for gemini direction matters...so either have to double add if tracking directions, or drop +/- if not
        } elsif ($vals[1] eq 'X+'){
#	    $type = "Xp";
	    $type = "X";
        } elsif ($vals[1] eq 'X_'){
#	    $type = "Xm";
	    $type = "X";
        } elsif ($vals[1] eq 'Y+'){
#	    $type = "Yp";
	    $type = "Y";
        } elsif ($vals[1] eq 'Y_'){
#	    $type = "Ym";
	    $type = "Y";
        } elsif ($vals[1] eq 'Z+'){
#	    $type = "Zp";
	    $type = "Z";
        } elsif ($vals[1] eq 'Z_'){
#	    $type = "Zm";
	    $type = "Z";
	} else {
	    $type = "UNK";
	}

	#first entry should always be a valid tile
	if (($vals[0] =~ /(.*)\[/) || ($vals[0] =~ /(.*\d)\(/)){
	    $E0 = $1;
	    if ($E0 =~ /(.*)l/){
		$R0 = $1;
		addTile($R0,$E0,$arch);
	    }
	}

	if (($vals[3] =~ /(.*)\[/) || ($vals[3] =~ /(.*\d)\(/)){
	    # this is a 2-ended link
	    $E1 = $1;
	    if ($E1 =~ /(.*)l/){
		$R1 = $1;
		#dont add the router for this side; will pick it up on the other side of the link
	    }

	    # these will readin as double, one for each endpoint, so check to see if we already have this one
	    my $lname0 = "link" . $E0;
	    my $lname1 = "link" . $E1;
	    if (!(exists $HoHlink{$lname0}) && !(exists $HoHlink{$lname1})){
		#add this link, otherwise we already have it from the other end
		#NOTE: for gemini direction matters...so either have to double add if tracking directions, or drop +/- if not
		addEndpoint($E0,"TLE",$lname0,"N/A");
		addEndpoint($E1,"TLE",$lname0,"N/A");
		addLink($R0,$E0,$R1,$E1,$lname0,$type);
	    }
	} elsif ($vals[3] =~ /unused/){ # only happens for Aries
	    #$E1 = "unused"; does not matter
	    #$R1 = "unused"; does not matter
	    #add the tile, but not the link
	    addTile($R0,$E0,$arch);
	    addEndpoint($E0,"TLE","N/A","N/A");
	} elsif ($vals[3] =~ /processor/){
	    if ($arch  eq "XC"){
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
		    addTile($R0,$E0,$arch);
		    addEndpoint($E0,"TLE",$lname0,"N/A");
		    addLink($R0,$E0,$R1,$E1,$lname0,$type); #add the ptile link
		    addAriesNIC($R1,$E1,$node,$lname0); #add the NIC, NODE, and pcie link
		}
	    } else {  # for gemini, the NIC facing tiles must be inferred
		die "Can't handle processor tiles for Gemini";
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
close($fh);

if ($arch eq "XE"){
# put ptiles in here
}

printCabinet();
printChassis();
printAriesSlot();
printAries();
printLink();
printEndpoint();
printPcieLink();



