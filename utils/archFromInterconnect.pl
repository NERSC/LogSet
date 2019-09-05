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
my %HoHlink; # for each link --  e1, e2, type. name of the link will be name of the tile. 
my %HoHPcieLink; # between node and NIC
my %HoHendpoint; #for each link endpoint, which it its link(s)? nodes, NICs, and tiles all go in here
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

sub getLinkname{
    my ($a, $b, $type) = @_;

    if ($type eq "PTL"){
	#this will always be link and NIC
#	return "ptile" . $a . "x" . $b;
	return "link" . $a;
    } else {

	$a =~ /c(\d+)_(\d+)c(\d+)s(\d+)/;
	my $arow = $1;
	my $acol = $2;
	my $achassis = $3;
	my $aslot = $4;

	$b =~ /c(\d+)_(\d+)c(\d+)s(\d+)/;
	my $brow = $1;
	my $bcol = $2;
	my $bchassis = $3;
	my $bslot = $4;
	
	my $name;
	if ($arow < $brow){
#	    $name = "link" . $a . "x" . $b;
	    $name = "link" . $a; 
	} elsif ($arow > $brow){
#	    $name = "link" . $b . "x" . $a;
	    $name = "link" . $b;
	} elsif ($acol < $bcol){
#	    $name = "link" . $a . "x" . $b;
	    $name = "link" . $a; 
	} elsif ($acol > $bcol){
#	    $name = "link" . $b . "x" . $a;
	    $name = "link" . $b;
	} elsif ($achassis < $bchassis){
#	    $name = "link" . $a . "x" . $b;
	    $name = "link" . $a; 
	} elsif ($achassis > $bchassis){
#	    $name = "link" . $b . "x" . $a;
	    $name = "link" . $b;
	} elsif ($aslot < $bslot){
#	    $name = "link" . $a . "x" . $b;
	    $name = "link" . $a; 
	} elsif($aslot > $bslot){
#	    $name = "link" . $b . "x" . $a;
	    $name = "link" . $b;
	}

	return $name;
    }
}


sub addLink{
    my ($R0,$E0,$R1,$E1,$lname0,$type) = @_;
    #add this link. ok if duplicate
    $HoHlink{$lname0}{'E0'} = $E0;
    $HoHlink{$lname0}{'E1'} = $E1;
    $HoHlink{$lname0}{'R0'} = $R0;
    $HoHlink{$lname0}{'R1'} = $R1;
    $HoHlink{$lname0}{'type'} = $type;
}

sub addEndpoint{
    my ($E0,$type,$lname0) = @_;
    $HoHendpoint{$E0}{'type'} = $type; # ok if this is a repeat

    if ($lname0 eq "N/A"){
	return; # unused
    }

    # can be an endpoint of multiple links (e.g., the NIC is an endpoint of three things)
    my @arr;
    if (exists $HoHendpoint{$E0}{'links'} ){
	@arr =  @{$HoHendpoint{$E0}{'links'}};
	#don't add it if we already have it for this endpoint
	my $found = 0;
	foreach my $val (@arr){
	    if (!($val cmp $lname0)){
		$found = 1;
	    }
	}
	if (!$found){
#	    print "adding $lname0 for endpoint $E0\n";
	    push @arr, $lname0;
	}
    } else {
#	print "adding $lname0 for endpoint $E0\n";
	$arr[0] = $lname0;
    }
    @{$HoHendpoint{$E0}{'links'}} = @arr;
}

sub printEndpoint{
    foreach (sort { $a <=> $b || $a cmp $b } keys(%HoHendpoint) ){
	my $ep = $_;

	if ($HoHendpoint{$ep}{'type'} =~ /PTL/){
	    print ":$ep a craydict:PTile ;";
	} elsif ($HoHendpoint{$ep}{'type'} =~ /NET/){
	    print ":$ep a craydict:NetworkTile ;";
	} elsif ($HoHendpoint{$ep}{'type'} =~ /NIC/){
	    print ":$ep a ddict:NIC ;";
	} elsif ($HoHendpoint{$ep}{'type'} =~ /NDE/){
	    print ":$ep a ddict:ComputeNode ;";
	}

	if (exists $HoHendpoint{$ep}{'links'}){
	    foreach my $val ( @{$HoHendpoint{$ep}{'links'}} ){
		print "\n\tlogset:endPointOf :" . $val . ";";
	    }
	} else {
#	    print "no endpoints for <$ep>\n";
	}
	print "\t.\n";
    }    
    print "\n";

}

sub addTile{
    #ok if duplicates come in
    my ($R0,$E0,$arch,$type) = @_;
    if ($arch =~ /XC/){
	$HoHaries{$R0}{$E0} = $type; #child of the aries
#    } else {
#	$HoHgemini{$R0}{$E0} = "TLE"; #child of the gemini DNE yet.....
    }
}


sub addNICandNode{
    my ($R0,$NIC,$nodenum,$lname0) = @_;

    if (!(exists $HoHaries{$R0}{$NIC})){ 
	$HoHaries{$R0}{$NIC} = "NIC"; #child of the aries. 
	#add the node
	if ($R0 =~ /(.*)a0/){
	    my $base = $1;
	    my $node = $base . "n". $nodenum;
	    my $pcie = "pcie" . $node;
	    #node is an enpoint
	    $HoHPcieLink{$pcie} = 1;
	    my @endarr = ();
	    
#	    print "adding endpint <$NIC> to link $pcie\n";
	    addEndpoint($NIC,"NIC",$pcie); #endpoint of the pcie. this will be unique to the NIC
#	    print "adding endpint <$node> to link $pcie\n";
	    addEndpoint($node,"NDE",$pcie); #endpoint of the pcie. this will be unique to the node
	}
    }
#    print "adding endpint <$NIC> to link $lname0\n";
    addEndpoint($NIC,"NIC",$lname0);     # add this ptile endpoint to the NIC, will be multiples
}


sub printCabinet{
    foreach my $cab (sort { $a <=> $b || $a cmp $b } keys(%HoHcabinet) ){
	print ":$cab a ddict:Cabinet ;\n";
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
    
	print ":$chassis a ddict:Chassis ;\n";
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
	print ":$slot a ddict:Blade ;\n";

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
	print ":$aries a craydict:AriesRouter ;\n";
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
	print ":$link a ddict:PCIeLink .\n";
    }
    print "\n";
}
    

sub printLink{
    foreach (sort { $a <=> $b || $a cmp $b } keys(%HoHlink) ){
	my $link = $_;

	if ($HoHlink{$link}{'type'} =~ /BLU/){
	    print ":$link a craydict:BlueLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /GRE/){
	    print ":$link a craydict:GreenLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /BLK/){
	    print ":$link a craydict:BlackLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /PTL/){
	    print ":$link a craydict:PtileLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /Xp/){
	    print ":$link a craydict:XpLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /Xm/){
	    print ":$link a craydict:XmLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /Yp/){
	    print ":$link a craydict:YpLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /Ym/){
	    print ":$link a craydict:YmLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /Zp/){
	    print ":$link a craydict:ZpLink .\n";
	} elsif ($HoHlink{$link}{'type'} =~ /Zm/){
	    print ":$link a craydict:ZmLink .\n";
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
#    print "<$line>\n";

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
	my $tiletype = -1;
	if ($vals[1] eq 'blue'){
	    $type = "BLU";
	    $tiletype = "NET";
	} elsif ($vals[1] eq 'black'){
	    $type = "BLK";
	    $tiletype = "NET";
	} elsif ($vals[1] eq 'green'){
	    $type = "GRE";
	    $tiletype = "NET";
	} elsif ($vals[1] eq 'ptile'){ # ptile only in the aries rtr output
	    $type = "PTL";
	    $tiletype = "PTL";
	} elsif ($vals[1] eq 'host'){ # DNE
	    $type = "HST";
	    $tiletype = "HST";
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
		addTile($R0,$E0,$arch,$tiletype);
	    }
	}

	if (($vals[3] =~ /(.*)\[/) || ($vals[3] =~ /(.*\d)\(/)){ 
	    # this is a 2-ended link, tile wise. (processor or unused are the other options)
	    $E1 = $1;
	    if ($E1 =~ /(.*)l/){
		$R1 = $1;
		# for Aries, the tiletype will be the same. NOTE: Gemini should be inverse
		addTile($R1,$E1,$arch,$tiletype);
	    }

	    # NEW: an Aries Link will still go in once, but it will be named by the two rtr endpoints, 
	    # in semi-alphabetical order not the linkname
	    
	    my $linkname = getLinkname($E0,$E1,$type); # need tiles, since there are 3 blacks with same endpoints
	    #TODO: decide what to do with gemini (since those have directions). Does that go in double or drop the +/- ?
	    addEndpoint($E0,$tiletype,$linkname);
	    addEndpoint($E1,$tiletype,$linkname);
	    addLink($R0,$E0,$R1,$E1,$linkname,$type);
	} elsif ($vals[3] =~ /unused/){ # only happens for Aries
	    #$E1 = "unused"; does not matter
	    #$R1 = "unused"; does not matter
	    #add the tile, but not the link
	    addTile($R0,$E0,$arch,$tiletype); #include the type, even if unused
	    addEndpoint($E0,$tiletype,"N/A");
	} elsif ($vals[3] =~ /processor/){
	    if ($arch  eq "XC"){
		# This endpoint is a NIC. aries has 4 NIC and 8 ptiles, in order. get the last digit
		# NIC will be endpoint of 2 ptilelinks and 1 pcie link.
		my $node = -1;
		if ($E0 =~ /.*(\d)/){
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
#		    print "adding ptile <$E0>\n";
		    addTile($R0,$E0,$arch,$tiletype);
		    my $linkname = getLinkname($E0,$E1,$type); #ptile link name includes the tile
#		    print "adding endpoint <$E0> to link $linkname\n";
		    addEndpoint($E0,$tiletype,$linkname); # add tile as endpoint
		    addLink($R0,$E0,$R1,$E1,$linkname,$type); #add the ptile link. 
		    addNICandNode($R1,$E1,$node,$linkname); # if DNE
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

print "\@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n";
print "\@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n";
print "\@prefix adms: <http://www.w3.org/ns/adms#> .\n";
print "\@prefix dct: <http://purl.org/dc/terms/> .\n";
print "\@base <https://portal.nersc.gov/project/m888/resilience/datasets/> .\n";
print "\@prefix logset: <logset#> .\n";
print "\@prefix ddict: <ddict#> .\n";
print "\n";
print "\@base <https://portal.nersc.gov/project/m888/resilience/datasets/> .\n";
print "\@prefix craydict: <cray-dict#> .\n";
print "\n";
print "# declare myself and set a prefix:\n";
print "\@base <https://portal.nersc.gov/project/m888/resilience/datasets/> .\n";
print "\@prefix : <FIXME-edison-arch#> .\n";
print "\n";
print ":\n";
print "\ta adms:Asset ;\n";
print "\tdct:title \"FIXME give this file a title\" ;\n";
print "\trdfs:label \"FIXME short label\" ;\n";
print "\t.\n";
print "\n";

printCabinet();
printChassis();
printAriesSlot();
printAries();
printLink();
printEndpoint();
printPcieLink();



