//Maya ASCII 2018 scene
//Name: Wolfen.ma
//Last modified: Thu, Dec 24, 2020 12:23:41 PM
//Codeset: 1252
requires maya "2018";
currentUnit -l centimeter -a degree -t ntsc;
fileInfo "application" "maya";
fileInfo "product" "Maya 2018";
fileInfo "version" "2018";
fileInfo "cutIdentifier" "201706261615-f9658c4cfc";
fileInfo "osv" "Microsoft Windows 8 , 64-bit  (Build 9200)\n";
createNode transform -s -n "persp";
	rename -uid "EA8C7F12-44DF-BCE1-CC8E-98A08399C764";
	setAttr ".v" no;
	setAttr ".t" -type "double3" -33.114150392606859 2.6803343340786783 -2.4103424299423217 ;
	setAttr ".r" -type "double3" 2.0616472704143951 -94.599999999998445 0 ;
createNode camera -s -n "perspShape" -p "persp";
	rename -uid "A014481E-4F73-7CE1-D4EF-C1923C802BAA";
	setAttr -k off ".v" no;
	setAttr ".fl" 34.999999999999993;
	setAttr ".coi" 36.057244015962013;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -s -n "top";
	rename -uid "6B6DB75F-4213-5CBF-77E8-E0A241043899";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 1000.1 0 ;
	setAttr ".r" -type "double3" -89.999999999999986 0 0 ;
createNode camera -s -n "topShape" -p "top";
	rename -uid "FB96735F-44F6-196F-626B-348429179CD9";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "top";
	setAttr ".den" -type "string" "top_depth";
	setAttr ".man" -type "string" "top_mask";
	setAttr ".hc" -type "string" "viewSet -t %camera";
	setAttr ".o" yes;
createNode transform -s -n "front";
	rename -uid "E3DDF567-4FCF-D86B-B3B0-52931CFEFD2B";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 0 1000.1 ;
createNode camera -s -n "frontShape" -p "front";
	rename -uid "58AC6E33-40D5-7EAA-C83E-76A81AB0DB90";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "front";
	setAttr ".den" -type "string" "front_depth";
	setAttr ".man" -type "string" "front_mask";
	setAttr ".hc" -type "string" "viewSet -f %camera";
	setAttr ".o" yes;
createNode transform -s -n "side";
	rename -uid "CBCA033C-4AFD-E21B-D1A6-AAB17D13DC1C";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 1000.1 0 0 ;
	setAttr ".r" -type "double3" 0 89.999999999999986 0 ;
createNode camera -s -n "sideShape" -p "side";
	rename -uid "21824A15-43B7-B79D-EB51-AEA04F722DB1";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "side";
	setAttr ".den" -type "string" "side_depth";
	setAttr ".man" -type "string" "side_mask";
	setAttr ".hc" -type "string" "viewSet -s %camera";
	setAttr ".o" yes;
createNode joint -n "JOBJ_0";
	rename -uid "E14A6435-4124-78FC-E15E-4AB6063ECD33";
	addAttr -ci true -h true -sn "fbxID" -ln "filmboxTypeID" -at "short";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -min 0 -max 1 -at "bool";
	setAttr ".ssc" no;
	setAttr ".bps" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".radi" 3;
	setAttr ".fbxID" 5;
createNode joint -n "JOBJ_1" -p "JOBJ_0";
	rename -uid "C38E07E1-4805-CB0D-C72F-9F8F25D6BFEE";
	addAttr -ci true -h true -sn "fbxID" -ln "filmboxTypeID" -at "short";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -min 0 -max 1 -at "bool";
	setAttr ".ssc" no;
	setAttr ".bps" -type "matrix" 0.62044299999999997 -0.57183700000000004 0.53670499999999999 0
		 0.45949499999999999 0.81964800000000004 0.34211399999999997 0 -0.63554299999999997 0.034350899999999997 0.77130100000000001 0
		 2.6291910000000001 7.3291579999999996 -3.8642370000000001 1;
	setAttr ".radi" 3;
	setAttr ".fbxID" 5;
createNode transform -n "Joint_1_Object_0_SINGLE";
	rename -uid "7BF4BA10-4E05-29E1-71C8-3282940D587F";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_0_SINGLEShape" -p "Joint_1_Object_0_SINGLE";
	rename -uid "DD1BFD26-4F8F-3369-DEAC-15A390CEA8A3";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_0_SINGLEShapeOrig" -p "Joint_1_Object_0_SINGLE";
	rename -uid "C3DCF500-4DBA-C92B-6B10-D6A50D8DCD98";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 15 ".uvst[0].uvsp[0:14]" -type "float2" 0.39453101 -1 0.55468798
		 1 0.71484399 -1 0.71484399 -1 0.55468798 1 0.83203101 -0.92968798 0.83203101 -0.92968798
		 0.55468798 1 1 -0.71093798 0.55468798 1 0.25390601 -0.92968798 0 -0.71093798 0.25390601
		 -0.92968798 0.55468798 1 0.39453101 -1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 15 ".vt[0:14]"  1.25864995 8.8160696 -0.207984 -0.91474402 8.4080801 1.38215995
		 0.93388402 9.11538982 -0.48891601 0.93388402 9.11538982 -0.48891601 -0.91474402 8.4080801 1.38215995
		 0.701841 9.11942959 -0.609393 0.701841 9.11942959 -0.609393 -0.91474402 8.4080801 1.38215995
		 0.216932 8.81867027 -0.81323701 -0.91474402 8.4080801 1.38215995 1.28834999 8.57886028 -0.102039
		 1.099120021 8.0055904388 -0.050108001 1.28834999 8.57886028 -0.102039 -0.91474402 8.4080801 1.38215995
		 1.25864995 8.8160696 -0.207984;
	setAttr -s 15 ".ed[0:14]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 0 9 10 0 10 11 0 11 9 0 12 13 0 13 14 0 14 12 0;
	setAttr -s 15 ".n[0:14]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 5 -ch 15 ".fc[0:4]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 11
		mu 0 3 9 10 11
		f 3 12 13 14
		mu 0 3 12 13 14;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_1_SINGLE";
	rename -uid "72ACA3D8-46AC-29DC-E6D0-2DA5EDC74199";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_1_SINGLEShape" -p "Joint_1_Object_1_SINGLE";
	rename -uid "B98E0116-43C6-E0F7-612F-57B7BFA0AABD";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_1_SINGLEShapeOrig" -p "Joint_1_Object_1_SINGLE";
	rename -uid "56A1D2D5-4F9A-29D9-A87D-D0876C4C3737";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 38 ".uvst[0].uvsp[0:37]" -type "float2" 0.58593798 1 0.55468798
		 1 0.55468798 0.87890601 0.44531301 0.87890601 0.44531301 1 0.41406301 1 0.55468798
		 0.87890601 0.55468798 1 0.44531301 1 0.44531301 0.87890601 0.58203101 0.91406298
		 0.53125 0.91406298 0.52734399 1 0.5625 1 0.328125 0.93359399 0.32421899 1 0.4375
		 1 0.41796899 0.91406298 0.46875 0.91406298 0.41796899 0.91406298 0.4375 1 0.47265601
		 1 0.46875 0.91406298 0.47265601 1 0.52734399 1 0.53125 0.91406298 0.67578101 1 0.671875
		 0.93359399 0.58203101 0.91406298 0.5625 1 0.71093798 0.93359399 0.671875 0.93359399
		 0.67578101 1 0.703125 1 0.328125 0.93359399 0.28906301 0.93359399 0.296875 1 0.32421899
		 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 38 ".vt[0:37]"  2.57766008 6.84276009 -3.56596994 2.55799007 7.050280094 -3.59141994
		 1.99667001 6.87938976 -3.12459993 1.67190003 7.17870998 -3.40552998 2.2332201 7.34959984 -3.87235999
		 2.073549986 7.3073802 -4.0020499229 1.99667001 6.87938976 -3.12459993 2.55799007 7.050280094 -3.59141994
		 2.2332201 7.34959984 -3.87235999 1.67190003 7.17870998 -3.40552998 2.40102005 7.13992023 -3.081559896
		 2.43210006 7.60387993 -3.081680059 2.67660999 7.48481989 -3.51303005 2.65814996 7.17648983 -3.51451993
		 1.72537994 7.8153801 -3.81523991 1.95170999 7.81787014 -4.12517023 2.29460001 7.51154995 -3.82898998
		 1.92114997 7.58220005 -3.49667001 2.25760007 7.76470995 -3.23263001 1.92114997 7.58220005 -3.49667001
		 2.29460001 7.51154995 -3.82898998 2.51664996 7.63224983 -3.65140009 2.25760007 7.76470995 -3.23263001
		 2.51664996 7.63224983 -3.65140009 2.67660999 7.48481989 -3.51303005 2.43210006 7.60387993 -3.081680059
		 2.99386001 6.85735989 -3.22368002 2.7335999 6.88613987 -2.94308996 2.40102005 7.13992023 -3.081559896
		 2.65814996 7.17648983 -3.51451993 2.99057007 7.023230076 -2.7374599 2.7335999 6.88613987 -2.94308996
		 2.99386001 6.85735989 -3.22368002 3.17497993 6.95750999 -3.078890085 1.72537994 7.8153801 -3.81523991
		 1.74483001 8.17136955 -3.8150599 1.96802998 8.069910049 -4.12296009 1.95170999 7.81787014 -4.12517023;
	setAttr -s 46 ".ed[0:45]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 1 8 9 0 9 6 0 10 11 0 11 12 0 12 10 1 12 13 0 13 10 0 14 15 0 15 16 0 16 14 1
		 16 17 0 17 14 0 18 19 0 19 20 0 20 18 1 20 21 0 21 18 0 22 23 0 23 24 0 24 22 1 24 25 0
		 25 22 0 26 27 0 27 28 0 28 26 1 28 29 0 29 26 0 30 31 0 31 32 0 32 30 1 32 33 0 33 30 0
		 34 35 0 35 36 0 36 34 1 36 37 0 37 34 0;
	setAttr -s 38 ".n[0:37]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 18 -ch 54 ".fc[0:17]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 -9
		mu 0 3 8 9 6
		f 3 11 12 13
		mu 0 3 10 11 12
		f 3 14 15 -14
		mu 0 3 12 13 10
		f 3 16 17 18
		mu 0 3 14 15 16
		f 3 19 20 -19
		mu 0 3 16 17 14
		f 3 21 22 23
		mu 0 3 18 19 20
		f 3 24 25 -24
		mu 0 3 20 21 18
		f 3 26 27 28
		mu 0 3 22 23 24
		f 3 29 30 -29
		mu 0 3 24 25 22
		f 3 31 32 33
		mu 0 3 26 27 28
		f 3 34 35 -34
		mu 0 3 28 29 26
		f 3 36 37 38
		mu 0 3 30 31 32
		f 3 39 40 -39
		mu 0 3 32 33 30
		f 3 41 42 43
		mu 0 3 34 35 36
		f 3 44 45 -44
		mu 0 3 36 37 34;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_2_SINGLE";
	rename -uid "64E07C37-4728-346A-BDD0-14A2EDA2AF61";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_2_SINGLEShape" -p "Joint_1_Object_2_SINGLE";
	rename -uid "E039D720-46FD-6612-EC2F-F3B3D1AAF69B";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_2_SINGLEShapeOrig" -p "Joint_1_Object_2_SINGLE";
	rename -uid "EBBE9926-421F-1124-6467-75B872AD7070";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 4 ".uvst[0].uvsp[0:3]" -type "float2" 0.089842997 1 0.91015601
		 0 0.91015601 1 0.089842997 0;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 4 ".vt[0:3]"  -1.49605 7.62958002 0.431393 -0.79539597 7.44999981 1.016720057
		 -0.96770602 7.1426301 0.88843101 -1.32374001 7.93695021 0.55968601;
	setAttr -s 5 ".ed[0:4]"  0 1 1 1 2 0 2 0 0 3 1 0 0 3 0;
	setAttr -s 4 ".n[0:3]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 2 -ch 6 ".fc[0:1]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 -1 4
		mu 0 3 3 1 0;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_3_SINGLE";
	rename -uid "ACBA029B-412C-1D4B-3741-5A965CDA9382";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_3_SINGLEShape" -p "Joint_1_Object_3_SINGLE";
	rename -uid "0AD92C66-49A1-AE01-A188-7FAEBC6926B2";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_3_SINGLEShapeOrig" -p "Joint_1_Object_3_SINGLE";
	rename -uid "73D58DDB-4799-5343-9264-D3858E32099F";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 8 ".uvst[0].uvsp[0:7]" -type "float2" 0.90625 -2 1 1 0
		 1 0.09375 -2 0.09375 -2 0 1 1 1 0.90625 -2;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 8 ".vt[0:7]"  -0.96770602 7.1426301 0.88843101 0.75390202 6.8056798 -1.27883005
		 0.104375 7.40431976 -1.84070003 -1.49605 7.62958002 0.431393 -1.32374001 7.93695021 0.55968601
		 0.47591999 8.067079544 -1.56406999 1.12545002 7.46844006 -1.0022000074 -0.79539597 7.44999981 1.016720057;
	setAttr -s 10 ".ed[0:9]"  0 1 0 1 2 0 2 0 1 2 3 0 3 0 0 4 5 0 5 6 0
		 6 4 1 6 7 0 7 4 0;
	setAttr -s 8 ".n[0:7]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 4 -ch 12 ".fc[0:3]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 -3
		mu 0 3 2 3 0
		f 3 5 6 7
		mu 0 3 4 5 6
		f 3 8 9 -8
		mu 0 3 6 7 4;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_4_SINGLE";
	rename -uid "62B13F98-4F3C-1CC7-F001-6E9C0CC8A596";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_4_SINGLEShape" -p "Joint_1_Object_4_SINGLE";
	rename -uid "C532E14C-4DDE-EEA9-EC2A-DD91A906785A";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_4_SINGLEShapeOrig" -p "Joint_1_Object_4_SINGLE";
	rename -uid "C026C2EA-44EF-0125-9FD8-ADA62B3A13DA";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 52 ".uvst[0].uvsp[0:51]" -type "float2" 0.050781 0.86718798
		 1 0.99218798 0.0039059999 1.0078099966 0.050781 0.136719 0.0039059999 0 1 0.0078119999
		 0.050781 0.86718798 0.0039059999 1.0078099966 1 0.99218798 0.050781 0.136719 1 0.0078119999
		 0.0039059999 0 0.48046899 0.265625 0.0039059999 0.26953101 0.0039059999 0 1 0.0078119999
		 1 0.99218798 0.48046899 0.73828101 0.0039059999 0.74218798 0.0039059999 1.0078099966
		 0.48046899 0.73828101 0.48046899 0.265625 0.0039059999 0.26953101 0.0039059999 0.74218798
		 0.48046899 0.265625 0.48046899 0.73828101 0.0039059999 0.74218798 0.0039059999 0.26953101
		 0.48046899 0.265625 1 0.0078119999 0.0039059999 0 0.0039059999 0.26953101 0.48046899
		 0.73828101 1 0.99218798 0.0039059999 1.0078099966 0.0039059999 0.74218798 0.0039059999
		 0.74218798 0.0039059999 0.26953101 0.0039059999 0 0.0039059999 1.0078099966 0.0039059999
		 1.0078099966 0.0039059999 0 0.0039059999 0.26953101 0.0039059999 0.74218798 0.0039059999
		 1.0078099966 0.050781 0.86718798 0.050781 0.136719 0.0039059999 0 0.0039059999 0
		 0.050781 0.136719 0.050781 0.86718798 0.0039059999 1.0078099966;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 52 ".vt[0:51]"  -1.49605 7.62958002 0.431393 0.104375 7.40431976 -1.84070003
		 -1.68080997 7.63276005 0.46640199 -1.32374001 7.93695021 0.55968601 -1.44567001 8.052189827 0.64146799
		 0.47591999 8.067079544 -1.56406999 -0.96770602 7.1426301 0.88843101 -1.031280041 7.034120083 1.028270006
		 0.75390202 6.8056798 -1.27883005 -0.79539597 7.44999981 1.016720057 1.12545002 7.46844006 -1.0022000074
		 -0.796148 7.45354986 1.20333004 0.16469701 7.26294994 0.129682 -0.773606 7.27737999 1.22975004
		 -0.796148 7.45354986 1.20333004 1.12545002 7.46844006 -1.0022000074 0.104375 7.40431976 -1.84070003
		 -0.80453402 7.72406006 -0.68948901 -1.70334995 7.80892992 0.439982 -1.68080997 7.63276005 0.46640199
		 -0.80453402 7.72406006 -0.68948901 -0.64478803 8.0090198517 -0.57055098 -1.58308995 8.023449898 0.52951902
		 -1.70334995 7.80892992 0.439982 0.16469701 7.26294994 0.129682 0.00495 6.97799015 0.010744
		 -0.89386398 7.062860012 1.14022005 -0.773606 7.27737999 1.22975004 -0.64478803 8.0090198517 -0.57055098
		 0.47591999 8.067079544 -1.56406999 -1.44567001 8.052189827 0.64146799 -1.58308995 8.023449898 0.52951902
		 0.00495 6.97799015 0.010744 0.75390202 6.8056798 -1.27883005 -1.031280041 7.034120083 1.028270006
		 -0.89386398 7.062860012 1.14022005 -1.70334995 7.80892992 0.439982 -1.58308995 8.023449898 0.52951902
		 -1.44567001 8.052189827 0.64146799 -1.68080997 7.63276005 0.46640199 -1.031280041 7.034120083 1.028270006
		 -0.796148 7.45354986 1.20333004 -0.773606 7.27737999 1.22975004 -0.89386398 7.062860012 1.14022005
		 -1.031280041 7.034120083 1.028270006 -0.96770602 7.1426301 0.88843101 -0.79539597 7.44999981 1.016720057
		 -0.796148 7.45354986 1.20333004 -1.44567001 8.052189827 0.64146799 -1.32374001 7.93695021 0.55968601
		 -1.49605 7.62958002 0.431393 -1.68080997 7.63276005 0.46640199;
	setAttr -s 62 ".ed[0:61]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 0 9 10 0 10 11 0 11 9 0 12 13 0 13 14 0 14 12 1 14 15 0 15 12 0 16 17 0
		 17 18 0 18 16 1 18 19 0 19 16 0 20 21 0 21 22 0 22 20 1 22 23 0 23 20 0 24 25 0 25 26 0
		 26 24 1 26 27 0 27 24 0 28 29 0 29 30 0 30 28 1 30 31 0 31 28 0 32 33 0 33 34 0 34 32 1
		 34 35 0 35 32 0 36 37 0 37 38 0 38 36 1 38 39 0 39 36 0 40 41 0 41 42 0 42 40 1 42 43 0
		 43 40 0 44 45 0 45 46 0 46 44 1 46 47 0 47 44 0 48 49 0 49 50 0 50 48 1 50 51 0 51 48 0;
	setAttr -s 52 ".n[0:51]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 24 -ch 72 ".fc[0:23]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 11
		mu 0 3 9 10 11
		f 3 12 13 14
		mu 0 3 12 13 14
		f 3 15 16 -15
		mu 0 3 14 15 12
		f 3 17 18 19
		mu 0 3 16 17 18
		f 3 20 21 -20
		mu 0 3 18 19 16
		f 3 22 23 24
		mu 0 3 20 21 22
		f 3 25 26 -25
		mu 0 3 22 23 20
		f 3 27 28 29
		mu 0 3 24 25 26
		f 3 30 31 -30
		mu 0 3 26 27 24
		f 3 32 33 34
		mu 0 3 28 29 30
		f 3 35 36 -35
		mu 0 3 30 31 28
		f 3 37 38 39
		mu 0 3 32 33 34
		f 3 40 41 -40
		mu 0 3 34 35 32
		f 3 42 43 44
		mu 0 3 36 37 38
		f 3 45 46 -45
		mu 0 3 38 39 36
		f 3 47 48 49
		mu 0 3 40 41 42
		f 3 50 51 -50
		mu 0 3 42 43 40
		f 3 52 53 54
		mu 0 3 44 45 46
		f 3 55 56 -55
		mu 0 3 46 47 44
		f 3 57 58 59
		mu 0 3 48 49 50
		f 3 60 61 -60
		mu 0 3 50 51 48;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_5_SINGLE";
	rename -uid "1A68F964-43DD-761F-41B6-7F8384198BA6";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_5_SINGLEShape" -p "Joint_1_Object_5_SINGLE";
	rename -uid "3D2BC01E-4FB3-F407-A03A-34A1ACC40835";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_5_SINGLEShapeOrig" -p "Joint_1_Object_5_SINGLE";
	rename -uid "9E14A5CE-4B92-C6AC-021D-EFB5B1656052";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 42 ".uvst[0].uvsp[0:41]" -type "float2" 2.79688001 1 0 -0.8125
		 1.63671994 -0.94921899 1.63671994 -2.050780058 0 -2.1875 2.79688001 -4 3 -2.82813001
		 2.79688001 -4 1.63671994 -2.050780058 1.63671994 -0.94921899 0 -0.8125 2.79688001
		 1 1.63671994 -2.050780058 2.79688001 -4 0 -2.1875 3 -2.30078006 1.63671994 -2.050780058
		 3 -2.25391006 1.63671994 -0.94921899 2.79688001 1 3 -0.171875 1.63671994 -2.050780058
		 2.79688001 -4 3 -2.82813001 3 -0.171875 2.79688001 1 1.63671994 -0.94921899 3 -2.82813001
		 1.63671994 -2.050780058 3 -2.30078006 3 -2.27343988 1.63671994 -2.050780058 3 -2.82813001
		 3 -0.171875 1.63671994 -0.94921899 3 -0.72656298 3 -0.69921899 1.63671994 -0.94921899
		 3 -0.171875 3 -0.74609399 1.63671994 -0.94921899 3 -0.69921899;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 42 ".vt[0:41]"  -0.19124401 8.76877022 -3.50234008 -0.80453402 7.72406006 -0.68948901
		 0.104375 7.40431976 -1.84070003 0.75390202 6.8056798 -1.27883005 0.00495 6.97799015 0.010744
		 2.76071 6.048079967 -0.94879198 2.28655005 6.86312008 -1.61381996 2.76071 6.048079967 -0.94879198
		 1.12545002 7.46844006 -1.0022000074 0.47591999 8.067079544 -1.56406999 -0.64478803 8.0090198517 -0.57055098
		 -0.19124401 8.76877022 -3.50234008 1.12545002 7.46844006 -1.0022000074 2.76071 6.048079967 -0.94879198
		 0.16469701 7.26294994 0.129682 2.026580095 7.2386899 -1.84475994 1.12545002 7.46844006 -1.0022000074
		 2.026220083 7.31672001 -1.84853995 0.47591999 8.067079544 -1.56406999 -0.19124401 8.76877022 -3.50234008
		 0.72089797 8.30611038 -2.96816993 0.75390202 6.8056798 -1.27883005 2.76071 6.048079967 -0.94879198
		 2.081929922 6.49811983 -1.76617002 0.51628 7.94111013 -3.12052011 -0.19124401 8.76877022 -3.50234008
		 0.104375 7.40431976 -1.84070003 2.28655005 6.86312008 -1.61381996 1.12545002 7.46844006 -1.0022000074
		 2.026580095 7.2386899 -1.84475994 1.66679001 6.64278984 -2.11468005 0.75390202 6.8056798 -1.27883005
		 2.081929922 6.49811983 -1.76617002 0.51628 7.94111013 -3.12052011 0.104375 7.40431976 -1.84070003
		 0.75551599 7.48266983 -2.90297008 1.08138001 8.10984993 -2.66240001 0.47591999 8.067079544 -1.56406999
		 0.72089797 8.30611038 -2.96816993 1.13917994 8.13426971 -2.61585999 0.47591999 8.067079544 -1.56406999
		 1.08138001 8.10984993 -2.66240001;
	setAttr -s 42 ".ed[0:41]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 0 9 10 0 10 11 0 11 9 0 12 13 0 13 14 0 14 12 0 15 16 0 16 17 0 17 15 0
		 18 19 0 19 20 0 20 18 0 21 22 0 22 23 0 23 21 0 24 25 0 25 26 0 26 24 0 27 28 0 28 29 0
		 29 27 0 30 31 0 31 32 0 32 30 0 33 34 0 34 35 0 35 33 0 36 37 0 37 38 0 38 36 0 39 40 0
		 40 41 0 41 39 0;
	setAttr -s 42 ".n[0:41]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 14 -ch 42 ".fc[0:13]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 11
		mu 0 3 9 10 11
		f 3 12 13 14
		mu 0 3 12 13 14
		f 3 15 16 17
		mu 0 3 15 16 17
		f 3 18 19 20
		mu 0 3 18 19 20
		f 3 21 22 23
		mu 0 3 21 22 23
		f 3 24 25 26
		mu 0 3 24 25 26
		f 3 27 28 29
		mu 0 3 27 28 29
		f 3 30 31 32
		mu 0 3 30 31 32
		f 3 33 34 35
		mu 0 3 33 34 35
		f 3 36 37 38
		mu 0 3 36 37 38
		f 3 39 40 41
		mu 0 3 39 40 41;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_6_SINGLE";
	rename -uid "08F35C89-4E48-70A2-6A7F-92BFE9389281";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_6_SINGLEShape" -p "Joint_1_Object_6_SINGLE";
	rename -uid "2E3DE17C-4839-3ECE-C2A9-AB8414097F99";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_6_SINGLEShapeOrig" -p "Joint_1_Object_6_SINGLE";
	rename -uid "1FADF187-4DE8-D5DE-C8EE-B4BDF66EAA44";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 12 ".uvst[0].uvsp[0:11]" -type "float2" 5.35547018 1 7 0.5
		 5.35547018 0 7 0.5 4.46093988 0.890625 4.46093988 0.109375 2.53906012 0.109375 2.53906012
		 0.890625 0 0.5 1.64453006 0 0 0.5 1.64453006 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 12 ".vt[0:11]"  2.081929922 6.49811983 -1.76617002 2.76071 6.048079967 -0.94879198
		 2.28655005 6.86312008 -1.61381996 2.76071 6.048079967 -0.94879198 0.00495 6.97799015 0.010744
		 0.16469701 7.26294994 0.129682 -0.64478803 8.0090198517 -0.57055098 -0.80453402 7.72406006 -0.68948901
		 -0.19124401 8.76877022 -3.50234008 0.72089797 8.30611038 -2.96816993 -0.19124401 8.76877022 -3.50234008
		 0.51628 7.94111013 -3.12052011;
	setAttr -s 12 ".ed[0:11]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 0 9 10 0 10 11 0 11 9 0;
	setAttr -s 12 ".n[0:11]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20;
	setAttr -s 4 -ch 12 ".fc[0:3]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 11
		mu 0 3 9 10 11;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_7_SINGLE";
	rename -uid "1A56E438-4FB7-26BB-8099-349FD4719E21";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_7_SINGLEShape" -p "Joint_1_Object_7_SINGLE";
	rename -uid "3531EFF1-4092-CCAE-EBAC-85AECCF6C170";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_7_SINGLEShapeOrig" -p "Joint_1_Object_7_SINGLE";
	rename -uid "863A8B4A-454F-9B96-D547-DC895F10EC7F";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 8 ".uvst[0].uvsp[0:7]" -type "float2" 0 1 1 0.9375 1 0.109375
		 0 0 1 0.9375 0 1 0 0 1 0.109375;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 8 ".vt[0:7]"  0.51628 7.94111013 -3.12052011 1.70074999 7.81608009 -4.33188009
		 1.86947 8.11703968 -4.2062602 0.72089797 8.30611038 -2.96816993 3.072510004 6.55178022 -3.1452601
		 2.081929922 6.49811983 -1.76617002 2.28655005 6.86312008 -1.61381996 3.24123001 6.85274982 -3.019639969;
	setAttr -s 10 ".ed[0:9]"  0 1 0 1 2 0 2 0 1 2 3 0 3 0 0 4 5 0 5 6 0
		 6 4 1 6 7 0 7 4 0;
	setAttr -s 8 ".n[0:7]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 4 -ch 12 ".fc[0:3]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 -3
		mu 0 3 2 3 0
		f 3 5 6 7
		mu 0 3 4 5 6
		f 3 8 9 -8
		mu 0 3 6 7 4;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_8_SINGLE";
	rename -uid "14FB8D3B-40C4-A6C0-C9E7-EAB7FD669CE9";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_8_SINGLEShape" -p "Joint_1_Object_8_SINGLE";
	rename -uid "D7A2FC97-4DD3-CFC2-FDE7-F4998346A24B";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_8_SINGLEShapeOrig" -p "Joint_1_Object_8_SINGLE";
	rename -uid "E4C4659D-4E39-C0D7-32C7-DF808CA4266A";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 25 ".uvst[0].uvsp[0:24]" -type "float2" 1 0.152344 1 0.85546899
		 0.58203101 0.375 0 0.5 0.77343798 0.25781301 0 0 0.58203101 1 0.58203101 0.375 1
		 0.85546899 0 0 0.58203101 0.375 0 0.52734399 0.77343798 0.25781301 1 0.28515601 1
		 0.152344 0.58203101 0.375 0 0 1 0.152344 1 0.152344 0 0 0.77343798 0.25781301 0 0.5
		 0.70703101 0.375 0.77343798 0.25781301 0 0.54296899;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 25 ".vt[0:24]"  3.072510004 6.55178022 -3.1452601 2.57766008 6.84276009 -3.56596994
		 2.28023005 6.61804008 -2.87930989 2.026580095 7.2386899 -1.84475994 2.99057007 7.023230076 -2.7374599
		 2.28655005 6.86312008 -1.61381996 1.99667001 6.87938976 -3.12459993 2.28023005 6.61804008 -2.87930989
		 2.57766008 6.84276009 -3.56596994 2.081929922 6.49811983 -1.76617002 2.28023005 6.61804008 -2.87930989
		 1.66679001 6.64278984 -2.11468005 2.99057007 7.023230076 -2.7374599 3.17497993 6.95750999 -3.078890085
		 3.24123001 6.85274982 -3.019639969 2.28023005 6.61804008 -2.87930989 2.081929922 6.49811983 -1.76617002
		 3.072510004 6.55178022 -3.1452601 3.24123001 6.85274982 -3.019639969 2.28655005 6.86312008 -1.61381996
		 2.99057007 7.023230076 -2.7374599 2.026580095 7.2386899 -1.84475994 2.89500999 7.17723989 -2.6812501
		 2.99057007 7.023230076 -2.7374599 2.026220083 7.31672001 -1.84853995;
	setAttr -s 26 ".ed[0:25]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 0 9 10 0 10 11 0 11 9 0 12 13 0 13 14 0 14 12 0 15 16 0 16 17 0 17 15 0
		 18 19 0 19 20 0 20 18 0 21 22 1 22 23 0 23 21 0 24 22 0 21 24 0;
	setAttr -s 25 ".n[0:24]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 9 -ch 27 ".fc[0:8]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 11
		mu 0 3 9 10 11
		f 3 12 13 14
		mu 0 3 12 13 14
		f 3 15 16 17
		mu 0 3 15 16 17
		f 3 18 19 20
		mu 0 3 18 19 20
		f 3 21 22 23
		mu 0 3 21 22 23
		f 3 24 -22 25
		mu 0 3 24 22 21;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_9_SINGLE";
	rename -uid "8876F366-4101-A2E2-366A-FDB5005A529E";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_9_SINGLEShape" -p "Joint_1_Object_9_SINGLE";
	rename -uid "9862DC7A-4B4B-E821-8126-638CF912CF14";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_9_SINGLEShapeOrig" -p "Joint_1_Object_9_SINGLE";
	rename -uid "F3497361-46C3-52F1-15A1-6F95662E8D47";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 25 ".uvst[0].uvsp[0:24]" -type "float2" 1 0.85546899 0.58203101
		 0.375 0.58203101 1 1 0.152344 0 0 0.58203101 0.375 0 0.52734399 0.58203101 0.375
		 0 0 1 0.152344 1 0.28515601 0.77343798 0.25781301 0.58203101 0.375 1 0.85546899 1
		 0.152344 0 0 1 0.152344 0.77343798 0.25781301 0.77343798 0.25781301 0 0.5 0 0 0 0.54296899
		 0.77343798 0.25781301 0.70703101 0.375 0 0.5;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 25 ".vt[0:24]"  2.073549986 7.3073802 -4.0020499229 1.38834 7.44006014 -3.65082002
		 1.67190003 7.17870998 -3.40552998 1.70074999 7.81608009 -4.33188009 0.51628 7.94111013 -3.12052011
		 1.38834 7.44006014 -3.65082002 0.75551599 7.48266983 -2.90297008 1.38834 7.44006014 -3.65082002
		 0.51628 7.94111013 -3.12052011 1.86947 8.11703968 -4.2062602 1.96802998 8.069910049 -4.12296009
		 1.74483001 8.17136955 -3.8150599 1.38834 7.44006014 -3.65082002 2.073549986 7.3073802 -4.0020499229
		 1.70074999 7.81608009 -4.33188009 0.72089797 8.30611038 -2.96816993 1.86947 8.11703968 -4.2062602
		 1.74483001 8.17136955 -3.8150599 1.74483001 8.17136955 -3.8150599 1.08138001 8.10984993 -2.66240001
		 0.72089797 8.30611038 -2.96816993 1.13917994 8.13426971 -2.61585999 1.74483001 8.17136955 -3.8150599
		 1.79469001 8.19136047 -3.63305998 1.08138001 8.10984993 -2.66240001;
	setAttr -s 26 ".ed[0:25]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 0 9 10 0 10 11 0 11 9 0 12 13 0 13 14 0 14 12 0 15 16 0 16 17 0 17 15 0
		 18 19 0 19 20 0 20 18 0 21 22 1 22 23 0 23 21 0 24 22 0 21 24 0;
	setAttr -s 25 ".n[0:24]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 9 -ch 27 ".fc[0:8]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 11
		mu 0 3 9 10 11
		f 3 12 13 14
		mu 0 3 12 13 14
		f 3 15 16 17
		mu 0 3 15 16 17
		f 3 18 19 20
		mu 0 3 18 19 20
		f 3 21 22 23
		mu 0 3 21 22 23
		f 3 24 -22 25
		mu 0 3 24 22 21;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_10_SINGLE";
	rename -uid "7D926764-4904-DAB9-28D8-3AAB50C53A76";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_10_SINGLEShape" -p "Joint_1_Object_10_SINGLE";
	rename -uid "F4950BC9-4CE7-445B-C98D-E685A3434678";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_10_SINGLEShapeOrig" -p "Joint_1_Object_10_SINGLE";
	rename -uid "3900E4AC-471A-C1F7-D21A-39941EB99D56";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 30 ".uvst[0].uvsp[0:29]" -type "float2" 0.67578101 0.0625
		 0.90234399 -1 0.5625 -1 0.4375 -1 0.097655997 -1 0.32421899 0.0625 0.046875 -0.77734399
		 0.13281301 0.078125 0.32421899 0.0625 0.097655997 -1 0.86718798 0.078125 0.953125
		 -0.77734399 0.90234399 -1 0.67578101 0.0625 0.36718801 0.0625 0.55859399 -0.6875
		 0.44140601 -0.6875 0.63281298 0.0625 0.61718798 0.5625 0.68359399 1 1 0.625 0.87890601
		 0.078125 1 -0.4375 0.94140601 -0.53125 0 0.625 0.058593001 -0.53125 0 -0.4375 0.121094
		 0.078125 0.31640601 1 0.38281301 0.5625;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 30 ".vt[0:29]"  2.40102005 7.13992023 -3.081559896 2.89500999 7.17723989 -2.6812501
		 2.43210006 7.60387993 -3.081680059 2.25760007 7.76470995 -3.23263001 1.79469001 8.19136047 -3.63305998
		 1.92114997 7.58220005 -3.49667001 1.74483001 8.17136955 -3.8150599 1.72537994 7.8153801 -3.81523991
		 1.92114997 7.58220005 -3.49667001 1.79469001 8.19136047 -3.63305998 2.7335999 6.88613987 -2.94308996
		 2.99057007 7.023230076 -2.7374599 2.89500999 7.17723989 -2.6812501 2.40102005 7.13992023 -3.081559896
		 2.29460001 7.51154995 -3.82898998 2.67660999 7.48481989 -3.51303005 2.51664996 7.63224983 -3.65140009
		 2.65814996 7.17648983 -3.51451993 2.55799007 7.050280094 -3.59141994 2.57766008 6.84276009 -3.56596994
		 3.072510004 6.55178022 -3.1452601 2.99386001 6.85735989 -3.22368002 3.24123001 6.85274982 -3.019639969
		 3.17497993 6.95750999 -3.078890085 1.70074999 7.81608009 -4.33188009 1.96802998 8.069910049 -4.12296009
		 1.86947 8.11703968 -4.2062602 1.95170999 7.81787014 -4.12517023 2.073549986 7.3073802 -4.0020499229
		 2.2332201 7.34959984 -3.87235999;
	setAttr -s 45 ".ed[0:44]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 1 8 9 0 9 6 0 10 11 0 11 12 0 12 10 1 12 13 0 13 10 0 14 15 1 15 16 0 16 14 0
		 14 17 1 17 15 0 18 17 1 14 18 1 19 17 1 18 19 0 20 17 1 19 20 0 20 21 1 21 17 0 22 21 1
		 20 22 0 22 23 0 23 21 0 24 25 1 25 26 0 26 24 0 24 27 1 27 25 0 28 27 1 24 28 0 28 14 1
		 14 27 0 29 18 0 14 29 1 28 29 0;
	setAttr -s 30 ".n[0:29]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20;
	setAttr -s 20 -ch 60 ".fc[0:19]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 -9
		mu 0 3 8 9 6
		f 3 11 12 13
		mu 0 3 10 11 12
		f 3 14 15 -14
		mu 0 3 12 13 10
		f 3 16 17 18
		mu 0 3 14 15 16
		f 3 19 20 -17
		mu 0 3 14 17 15
		f 3 21 -20 22
		mu 0 3 18 17 14
		f 3 23 -22 24
		mu 0 3 19 17 18
		f 3 25 -24 26
		mu 0 3 20 17 19
		f 3 27 28 -26
		mu 0 3 20 21 17
		f 3 29 -28 30
		mu 0 3 22 21 20
		f 3 31 32 -30
		mu 0 3 22 23 21
		f 3 33 34 35
		mu 0 3 24 25 26
		f 3 36 37 -34
		mu 0 3 24 27 25
		f 3 38 -37 39
		mu 0 3 28 27 24
		f 3 40 41 -39
		mu 0 3 28 14 27
		f 3 42 -23 43
		mu 0 3 29 18 14
		f 3 -44 -41 44
		mu 0 3 29 14 28;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_11_SINGLE";
	rename -uid "15AB7486-4277-B277-B207-88ADC30E1BE7";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_11_SINGLEShape" -p "Joint_1_Object_11_SINGLE";
	rename -uid "2280DCBD-407A-BD7B-F384-04B7C9D3D6E9";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_11_SINGLEShapeOrig" -p "Joint_1_Object_11_SINGLE";
	rename -uid "A943A302-4E1E-8F17-2EE5-508C00E1A63F";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 6 ".uvst[0].uvsp[0:5]" -type "float2" 0.75 1 0 1 0.75 0
		 0.75 1 0.75 0 0 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 6 ".vt[0:5]"  0.910133 7.23092985 0.107213 -1.10154998 8.1993103 1.87059999
		 1.15608001 7.85061979 0.039173 -0.48101699 8.51309967 -1.096179962 0.060605999 8.86026955 -0.90844798
		 -1.43115997 8.5031004 1.58546996;
	setAttr -s 6 ".ed[0:5]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0;
	setAttr -s 6 ".n[0:5]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 2 -ch 6 ".fc[0:1]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_12_SINGLE";
	rename -uid "53462256-4F97-73EC-1125-74A013A8FE47";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_12_SINGLEShape" -p "Joint_1_Object_12_SINGLE";
	rename -uid "942DFC7B-470B-43CB-76DC-90A4BF23B495";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_12_SINGLEShapeOrig" -p "Joint_1_Object_12_SINGLE";
	rename -uid "AC9D1415-420F-51AA-4EE5-E3A0739FA3B5";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 13 ".uvst[0].uvsp[0:12]" -type "float2" 0.78515601 0.69140601
		 0.703125 0.92578101 0.29296899 0.57031298 0.92578101 0.69140601 1 1 0.97265601 0.71875
		 0.92578101 0.30859399 0.97265601 0.28125 1 0 0.703125 0.074217997 0.78515601 0.30859399
		 0.29296899 0.42968801 0 0.5;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 13 ".vt[0:12]"  0.56762397 8.039030075 -1.69995999 -0.38334599 8.47998047 -1.35354996
		 -2.70436001 8.041359901 2.68909001 1.56810999 7.98496008 -2.91416001 1.7622 8.47336006 -4.21935987
		 1.75571001 8.20191002 -3.68590999 2.21762991 7.38632011 -2.35228992 2.92873001 7.12079 -2.67121005
		 3.47811007 6.89187002 -2.73503995 1.08051002 7.13079977 -0.087258004 1.21714997 7.44039011 -1.13810003
		 -2.45714998 7.81351995 2.90293002 -4.64390993 8.075240135 5.33853006;
	setAttr -s 26 ".ed[0:25]"  0 1 1 1 2 1 2 0 0 3 1 1 0 3 0 3 4 1 4 1 0
		 3 5 1 5 4 0 6 5 1 3 6 0 6 7 1 7 5 0 6 8 1 8 7 0 6 9 1 9 8 0 10 9 1 6 10 0 11 9 1
		 10 11 0 11 12 1 12 9 0 2 12 1 11 2 0 1 12 0;
	setAttr -s 13 ".n[0:12]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 13 -ch 39 ".fc[0:12]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 -1 4
		mu 0 3 3 1 0
		f 3 5 6 -4
		mu 0 3 3 4 1
		f 3 7 8 -6
		mu 0 3 3 5 4
		f 3 9 -8 10
		mu 0 3 6 5 3
		f 3 11 12 -10
		mu 0 3 6 7 5
		f 3 13 14 -12
		mu 0 3 6 8 7
		f 3 15 16 -14
		mu 0 3 6 9 8
		f 3 17 -16 18
		mu 0 3 10 9 6
		f 3 19 -18 20
		mu 0 3 11 9 10
		f 3 21 22 -20
		mu 0 3 11 12 9
		f 3 23 -22 24
		mu 0 3 2 12 11
		f 3 -2 25 -24
		mu 0 3 2 1 12;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_13_SINGLE";
	rename -uid "5BE265B7-4EAB-69BE-E4A5-D594C2CF08CB";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_13_SINGLEShape" -p "Joint_1_Object_13_SINGLE";
	rename -uid "19F1DADF-4D4B-833C-861E-0A86A8D805F0";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_13_SINGLEShapeOrig" -p "Joint_1_Object_13_SINGLE";
	rename -uid "346B1F73-4710-A58D-EB28-5CACB7AC86F9";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 4 ".uvst[0].uvsp[0:3]" -type "float2" 0 0 1 1 0 1 1 0;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 4 ".vt[0:3]"  -2.70436001 8.041359901 2.68909001 1.21714997 7.44039011 -1.13810003
		 0.56762397 8.039030075 -1.69995999 -2.45714998 7.81351995 2.90293002;
	setAttr -s 5 ".ed[0:4]"  0 1 1 1 2 0 2 0 0 3 1 0 0 3 0;
	setAttr -s 4 ".n[0:3]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 2 -ch 6 ".fc[0:1]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 -1 4
		mu 0 3 3 1 0;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_14_SINGLE";
	rename -uid "2244910E-49B9-3252-0AC1-2DA02B91D5A1";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_14_SINGLEShape" -p "Joint_1_Object_14_SINGLE";
	rename -uid "11AB60DF-473D-75A5-2ACF-719A0C31CAB3";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_14_SINGLEShapeOrig" -p "Joint_1_Object_14_SINGLE";
	rename -uid "0A6A516B-4E30-7015-1016-498D83860A93";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 26 ".uvst[0].uvsp[0:25]" -type "float2" 0 1 1 0.98828101
		 0.09375 -1 0.09375 -1 1 0.98828101 0 1 0 1 1 0.99218798 0.089842997 -1 0 1 1 0.98828101
		 0 1 0.089842997 -1 1 0.99218798 0 1 0 1 1 0.99218798 0 1 0 1 1 1 0.96093798 0.890625
		 0.63281298 0 0 1 0.63281298 0 0.96093798 0.890625 1 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 26 ".vt[0:25]"  0.87909901 9.47418976 -4.72317982 -3.40375996 13.046999931 -5.28146982
		 0.32212901 9.50360012 -3.85146999 0.32212901 9.50360012 -3.85146999 -3.40375996 13.046999931 -5.28146982
		 0.93716502 9.57120991 -4.67965984 4.33991003 6.43504 -1.73616004 6.26884985 4.13219976 3.085680008
		 3.60126996 6.48134995 -1.014889956 0.93716502 9.57120991 -4.67965984 -3.40375996 13.046999931 -5.28146982
		 0.87909901 9.47418976 -4.72317982 3.60126996 6.48134995 -1.014889956 6.26884985 4.13219976 3.085680008
		 4.28426981 6.33579016 -1.77759004 4.28426981 6.33579016 -1.77759004 6.26884985 4.13219976 3.085680008
		 4.33991003 6.43504 -1.73616004 -4.80623007 8.10050011 5.55310011 -0.361251 8.52050972 -1.42323995
		 -0.48101699 8.51309967 -1.096179962 -1.43115997 8.5031004 1.58546996 -4.80623007 8.10050011 5.55310011
		 -1.10154998 8.1993103 1.87059999 0.910133 7.23092985 0.107213 1.16077006 7.11773014 -0.106638;
	setAttr -s 28 ".ed[0:27]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 0 9 10 0 10 11 0 11 9 0 12 13 0 13 14 0 14 12 0 15 16 0 16 17 0 17 15 0
		 18 19 0 19 20 0 20 18 1 20 21 0 21 18 0 22 23 0 23 24 0 24 22 1 24 25 0 25 22 0;
	setAttr -s 26 ".n[0:25]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20;
	setAttr -s 10 -ch 30 ".fc[0:9]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 11
		mu 0 3 9 10 11
		f 3 12 13 14
		mu 0 3 12 13 14
		f 3 15 16 17
		mu 0 3 15 16 17
		f 3 18 19 20
		mu 0 3 18 19 20
		f 3 21 22 -21
		mu 0 3 20 21 18
		f 3 23 24 25
		mu 0 3 22 23 24
		f 3 26 27 -26
		mu 0 3 24 25 22;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_15_SINGLE";
	rename -uid "F5E46F05-4EFE-6DCB-CD28-AC828E5776B3";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_15_SINGLEShape" -p "Joint_1_Object_15_SINGLE";
	rename -uid "7B6C27D6-44D3-0DDF-BEBF-0F877E535C75";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_15_SINGLEShapeOrig" -p "Joint_1_Object_15_SINGLE";
	rename -uid "15424DBF-4911-3438-3968-D2B41F07692F";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 32 ".uvst[0].uvsp[0:31]" -type "float2" 0.078125 0.50390601
		 0.09375 0.421875 0.113281 0.41796899 0.113281 0.41796899 0.09375 0.421875 0.078125
		 0.50390601 0.058593001 0.97265601 0 0.93359399 0.042968001 0.6875 0.41796899 0.97656298
		 0.058593001 0.97265601 0.41796899 0.97656298 0.042968001 0.6875 0 0.93359399 0.078125
		 0.50390601 0.54296899 0.38281301 0.113281 0.41796899 0.54296899 0.44921899 1 0.128906
		 0.113281 0.41796899 0.54296899 0.44921899 0.078125 0.50390601 0.54296899 0.38281301
		 1 0.128906 0.54296899 0.44921899 0.078125 0.50390601 1 0.128906 0.6875 1 0.54296899
		 0.44921899 0.078125 0.50390601 0.6875 1 1 0.128906;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 32 ".vt[0:31]"  1.35745001 8.43642044 -0.013437 1.34587002 8.7119503 -0.121347
		 1.47836006 8.67171955 -0.157253 0.84822601 9.25249004 -0.702344 0.82237101 9.19443989 -0.574193
		 0.557661 9.17356014 -0.705284 1.16077006 7.11773014 -0.106638 0.910133 7.23092985 0.107213
		 1.15608001 7.85061979 0.039173 2.61144996 7.17808008 -1.53738999 -0.361251 8.52050972 -1.42323995
		 0.96824503 8.69254971 -2.95883012 0.060605999 8.86026955 -0.90844798 -0.48101699 8.51309967 -1.096179962
		 0.557661 9.17356014 -0.705284 2.48737001 9.48243046 -2.46142006 0.84822601 9.25249004 -0.702344
		 2.34187007 9.46434975 -2.61088991 4.79851007 9.73875999 -3.8046999 1.47836006 8.67171955 -0.157253
		 3.24345994 8.63339996 -1.83098996 1.35745001 8.43642044 -0.013437 3.19022012 8.83465004 -1.85343003
		 4.79851007 9.73875999 -3.8046999 3.24345994 8.63339996 -1.83098996 1.35745001 8.43642044 -0.013437
		 4.79851007 9.73875999 -3.8046999 3.52345991 7.3151598 -2.73677993 2.34187007 9.46434975 -2.61088991
		 0.557661 9.17356014 -0.705284 2.074150085 8.6509304 -3.99048996 4.79851007 9.73875999 -3.8046999;
	setAttr -s 46 ".ed[0:45]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 1 8 9 1 9 6 0 10 11 0 11 12 1 12 10 1 12 13 0 13 10 0 14 15 1 15 16 0 16 14 0
		 17 15 1 14 17 0 17 18 0 18 15 0 19 20 1 20 21 0 21 19 0 22 20 1 19 22 0 22 23 0 23 20 0
		 24 9 1 8 24 1 8 25 0 25 24 0 26 9 1 24 26 0 26 27 0 27 9 0 11 28 1 28 12 1 28 29 0
		 29 12 0 30 28 1 11 30 0 30 31 0 31 28 0;
	setAttr -s 32 ".n[0:31]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 20 -ch 60 ".fc[0:19]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 -9
		mu 0 3 8 9 6
		f 3 11 12 13
		mu 0 3 10 11 12
		f 3 14 15 -14
		mu 0 3 12 13 10
		f 3 16 17 18
		mu 0 3 14 15 16
		f 3 19 -17 20
		mu 0 3 17 15 14
		f 3 21 22 -20
		mu 0 3 17 18 15
		f 3 23 24 25
		mu 0 3 19 20 21
		f 3 26 -24 27
		mu 0 3 22 20 19
		f 3 28 29 -27
		mu 0 3 22 23 20
		f 3 30 -10 31
		mu 0 3 24 9 8
		f 3 -32 32 33
		mu 0 3 24 8 25
		f 3 34 -31 35
		mu 0 3 26 9 24
		f 3 36 37 -35
		mu 0 3 26 27 9
		f 3 38 39 -13
		mu 0 3 11 28 12
		f 3 -40 40 41
		mu 0 3 12 28 29
		f 3 42 -39 43
		mu 0 3 30 28 11
		f 3 44 45 -43
		mu 0 3 30 31 28;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_16_SINGLE";
	rename -uid "772C9378-4F2A-B7E8-F772-8DAD74056A27";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_16_SINGLEShape" -p "Joint_1_Object_16_SINGLE";
	rename -uid "BDE67305-499B-1ECC-EBCE-FBA6009802C3";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_16_SINGLEShapeOrig" -p "Joint_1_Object_16_SINGLE";
	rename -uid "542F2431-4E58-7183-7083-B29773E4F5AB";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 27 ".uvst[0].uvsp[0:26]" -type "float2" 0.546875 0.113281
		 0.546875 0.88671899 0.99218798 0.5 0.30468801 0.5 0.0625 0.1875 0.0625 0.8125 0.30468801
		 0.5 0.0625 0.8125 0.058593001 0.92578101 0.058593001 0.074217997 0.0625 0.1875 0.30468801
		 0.5 1.98046994 -0.21093801 0 1 0.28515601 0.21093801 2 -1 0.28515601 0.21093801 0
		 1 1.98046994 -0.21093801 2 -1 0.082030997 1 0.30468801 0.5 0.058593001 0.92578101
		 0.55078101 0.88671899 0.55078101 0.113281 0.082030997 0 0.058593001 0.074217997;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 27 ".vt[0:26]"  3.19022012 8.83465004 -1.85343003 2.48737001 9.48243046 -2.46142006
		 4.79851007 9.73875999 -3.8046999 1.97422004 9.053529739 -1.26984 1.32339001 8.80440998 -0.16424599
		 0.91137803 9.18414974 -0.520652 1.97422004 9.053529739 -1.26984 0.91137803 9.18414974 -0.520652
		 0.82237101 9.19443989 -0.574193 1.34587002 8.7119503 -0.121347 1.32339001 8.80440998 -0.16424599
		 1.97422004 9.053529739 -1.26984 1.15608001 7.85061979 0.039173 -1.25986004 8.36734962 1.73773003
		 -0.964396 8.41075993 1.44242001 1.12336004 7.98326015 -0.029143 -0.964396 8.41075993 1.44242001
		 -1.25986004 8.36734962 1.73773003 0.060605999 8.86026955 -0.90844798 0.19269601 8.84101009 -0.83420199
		 0.84822601 9.25249004 -0.702344 1.97422004 9.053529739 -1.26984 0.82237101 9.19443989 -0.574193
		 2.48737001 9.48243046 -2.46142006 3.19022012 8.83465004 -1.85343003 1.47836006 8.67171955 -0.157253
		 1.34587002 8.7119503 -0.121347;
	setAttr -s 33 ".ed[0:32]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 0 9 10 0 10 11 0 11 9 0 12 13 0 13 14 0 14 12 1 14 15 0 15 12 0 16 17 0
		 17 18 0 18 16 1 18 19 0 19 16 0 20 21 1 21 22 0 22 20 0 23 21 1 20 23 0 24 21 1 23 24 0
		 25 21 1 24 25 0 25 26 0 26 21 0;
	setAttr -s 27 ".n[0:26]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 13 -ch 39 ".fc[0:12]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 11
		mu 0 3 9 10 11
		f 3 12 13 14
		mu 0 3 12 13 14
		f 3 15 16 -15
		mu 0 3 14 15 12
		f 3 17 18 19
		mu 0 3 16 17 18
		f 3 20 21 -20
		mu 0 3 18 19 16
		f 3 22 23 24
		mu 0 3 20 21 22
		f 3 25 -23 26
		mu 0 3 23 21 20
		f 3 27 -26 28
		mu 0 3 24 21 23
		f 3 29 -28 30
		mu 0 3 25 21 24
		f 3 31 32 -30
		mu 0 3 25 26 21;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_17_SINGLE";
	rename -uid "BB56A5D1-4AD6-8A47-3713-DE8E60EAB881";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_17_SINGLEShape" -p "Joint_1_Object_17_SINGLE";
	rename -uid "30A9C70D-4B98-811B-3229-C39EEA315CA1";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_17_SINGLEShapeOrig" -p "Joint_1_Object_17_SINGLE";
	rename -uid "2E71EB1D-40FE-A2D2-DF58-D5A5A6DE1409";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 26 ".uvst[0].uvsp[0:25]" -type "float2" 0.63281298 0.66015601
		 0.984375 0.890625 0.63281298 0.54296899 1 1 1 0.03125 -0.0039059999 0.53125 0.984375
		 0.19531301 0.63281298 0.42578101 0.99218798 1.0625 1 1.085940003 0 0.54296899 0.03125
		 0.54296899 0 0.54296899 1 0.0039059999 0.99218798 0.023437001 0 0.54296899 0.73828101
		 0.15625 0.3125 0 0.6875 0 0.26171899 0.15625 0.921875 0.77734399 0.86718798 0.296875
		 1 1 0.078125 0.77734399 0 1 0.13281301 0.296875;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 26 ".vt[0:25]"  -1.43115997 8.5031004 1.58546996 0.060605999 8.86026955 -0.90844798
		 -1.25986004 8.36734962 1.73773003 0.19269601 8.84101009 -0.83420199 1.12336004 7.98326015 -0.029143
		 -0.964396 8.41075993 1.44242001 1.15608001 7.85061979 0.039173 -1.10154998 8.1993103 1.87059999
		 -0.38334599 8.47998047 -1.35354996 -0.361251 8.52050972 -1.42323995 -4.80623007 8.10050011 5.55310011
		 -4.64390993 8.075240135 5.33853006 -4.80623007 8.10050011 5.55310011 1.16077006 7.11773014 -0.106638
		 1.08051002 7.13079977 -0.087258004 -4.80623007 8.10050011 5.55310011 1.34587002 8.7119503 -0.121347
		 0.91137803 9.18414974 -0.520652 1.32339001 8.80440998 -0.16424599 0.82237101 9.19443989 -0.574193
		 1.12336004 7.98326015 -0.029143 1.35745001 8.43642044 -0.013437 1.15608001 7.85061979 0.039173
		 0.19269601 8.84101009 -0.83420199 0.060605999 8.86026955 -0.90844798 0.557661 9.17356014 -0.705284;
	setAttr -s 39 ".ed[0:38]"  0 1 0 1 2 0 2 0 1 3 4 0 4 5 0 5 3 0 2 6 0
		 6 7 0 7 2 1 8 9 0 9 10 0 10 8 1 10 11 0 11 8 0 11 12 0 12 13 0 13 11 1 13 14 0 14 11 0
		 15 0 0 2 15 1 7 15 0 16 17 1 17 18 0 18 16 0 16 19 1 19 17 0 16 20 1 20 19 1 21 20 1
		 16 21 0 21 22 0 22 20 0 23 19 1 20 23 0 24 19 1 23 24 0 24 25 0 25 19 0;
	setAttr -s 27 ".n[0:26]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 17 -ch 51 ".fc[0:16]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 2 6 7
		f 3 9 10 11
		mu 0 3 8 9 10
		f 3 12 13 -12
		mu 0 3 10 11 8
		f 3 14 15 16
		mu 0 3 11 12 13
		f 3 17 18 -17
		mu 0 3 13 14 11
		f 3 19 -3 20
		mu 0 3 15 0 2
		f 3 -9 21 -21
		mu 0 3 2 7 15
		f 3 22 23 24
		mu 0 3 16 17 18
		f 3 25 26 -23
		mu 0 3 16 19 17
		f 3 27 28 -26
		mu 0 3 16 20 19
		f 3 29 -28 30
		mu 0 3 21 20 16
		f 3 31 32 -30
		mu 0 3 21 22 20
		f 3 33 -29 34
		mu 0 3 23 19 20
		f 3 35 -34 36
		mu 0 3 24 19 23
		f 3 37 38 -36
		mu 0 3 24 25 19;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_18_SINGLE";
	rename -uid "0B0FF24F-4F58-0079-8B77-04B6B28C72E8";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_18_SINGLEShape" -p "Joint_1_Object_18_SINGLE";
	rename -uid "FB0CE96E-4626-67B9-CF39-9A9CB0CA5D2E";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_18_SINGLEShapeOrig" -p "Joint_1_Object_18_SINGLE";
	rename -uid "68A2DD87-4E6C-587C-AFFE-3AA1E51FC6FD";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 54 ".uvst[0].uvsp[0:53]" -type "float2" 0.99218798 -1 0.96093798
		 -0.96484399 0.066405997 0.26953101 0.066405997 0.26953101 0.96093798 -0.96484399
		 0.99218798 -1 0.99218798 -1 0.86328101 0.98828101 0 0.91796899 0 0.91796899 0.85546899
		 0.98828101 0.99218798 -1 0.0039059999 0 0 0.50781298 0.86328101 1 1 0.085937001 1
		 0 0 0.42578101 0.050781 0.44531301 0.9375 0.183594 0 0.42578101 1 1 0.9375 0.78906298
		 0.050781 0.44531301 1 1 1 0 0.9375 0.183594 0.9375 0.78906298 1 0 1 1 0.9375 0.78906298
		 0.9375 0.183594 1 1 0 0.42578101 0.050781 0.44531301 0.9375 0.78906298 0 0.42578101
		 1 0 0.9375 0.183594 0.050781 0.44531301 0 0 1 0.089842997 0.85546899 1 0 0.50781298
		 0.066405997 0.26953101 0.89843798 0.16406301 0.96093798 -0.96484399 0.0039059999
		 0.91796899 1 1 0.89453101 0.16406301 0.066405997 0.26953101 0.96093798 -0.96484399
		 1 1 0 0.91796899;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 54 ".vt[0:53]"  1.08051002 7.13079977 -0.087258004 1.16077006 7.11773014 -0.106638
		 3.54152989 6.50680017 -0.98421901 0.308438 9.48661041 -3.78096008 -0.361251 8.52050972 -1.42323995
		 -0.38334599 8.47998047 -1.35354996 -0.38334599 8.47998047 -1.35354996 1.7622 8.47336006 -4.21935987
		 0.93076098 9.41407967 -4.77415991 4.2898798 6.31812 -1.86839998 3.47811007 6.89187002 -2.73503995
		 1.08051002 7.13079977 -0.087258004 1.026520014 9.57833958 -4.70256996 0.93076098 9.41407967 -4.77415991
		 1.7622 8.47336006 -4.21935987 2.074150085 8.6509304 -3.99048996 1.026520014 9.57833958 -4.70256996
		 0.308438 9.48661041 -3.78096008 0.32212901 9.50360012 -3.85146999 0.93716502 9.57120991 -4.67965984
		 0.308438 9.48661041 -3.78096008 0.93076098 9.41407967 -4.77415991 0.87909901 9.47418976 -4.72317982
		 0.32212901 9.50360012 -3.85146999 0.93076098 9.41407967 -4.77415991 1.026520014 9.57833958 -4.70256996
		 0.93716502 9.57120991 -4.67965984 0.87909901 9.47418976 -4.72317982 4.38321018 6.48461008 -1.79891002
		 4.2898798 6.31812 -1.86839998 4.28426981 6.33579016 -1.77759004 4.33991003 6.43504 -1.73616004
		 4.2898798 6.31812 -1.86839998 3.54152989 6.50680017 -0.98421901 3.60126996 6.48134995 -1.014889956
		 4.28426981 6.33579016 -1.77759004 3.54152989 6.50680017 -0.98421901 4.38321018 6.48461008 -1.79891002
		 4.33991003 6.43504 -1.73616004 3.60126996 6.48134995 -1.014889956 4.38321018 6.48461008 -1.79891002
		 3.52345991 7.3151598 -2.73677993 3.47811007 6.89187002 -2.73503995 4.2898798 6.31812 -1.86839998
		 0.308438 9.48661041 -3.78096008 0.96824503 8.69254971 -2.95883012 -0.361251 8.52050972 -1.42323995
		 1.026520014 9.57833958 -4.70256996 2.074150085 8.6509304 -3.99048996 2.61144996 7.17808008 -1.53738999
		 3.54152989 6.50680017 -0.98421901 1.16077006 7.11773014 -0.106638 3.52345991 7.3151598 -2.73677993
		 4.38321018 6.48461008 -1.79891002;
	setAttr -s 66 ".ed[0:65]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 0 9 10 0 10 11 0 11 9 0 12 13 0 13 14 0 14 12 1 14 15 0 15 12 0 16 17 0
		 17 18 0 18 16 1 18 19 0 19 16 0 20 21 0 21 22 0 22 20 1 22 23 0 23 20 0 24 25 0 25 26 0
		 26 24 1 26 27 0 27 24 0 28 29 0 29 30 0 30 28 1 30 31 0 31 28 0 32 33 0 33 34 0 34 32 1
		 34 35 0 35 32 0 36 37 0 37 38 0 38 36 1 38 39 0 39 36 0 40 41 0 41 42 0 42 40 1 42 43 0
		 43 40 0 44 45 1 45 46 0 46 44 0 47 45 1 44 47 0 47 48 0 48 45 0 49 50 1 50 51 0 51 49 0
		 52 50 1 49 52 0 52 53 0 53 50 0;
	setAttr -s 54 ".n[0:53]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20;
	setAttr -s 26 -ch 78 ".fc[0:25]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 11
		mu 0 3 9 10 11
		f 3 12 13 14
		mu 0 3 12 13 14
		f 3 15 16 -15
		mu 0 3 14 15 12
		f 3 17 18 19
		mu 0 3 16 17 18
		f 3 20 21 -20
		mu 0 3 18 19 16
		f 3 22 23 24
		mu 0 3 20 21 22
		f 3 25 26 -25
		mu 0 3 22 23 20
		f 3 27 28 29
		mu 0 3 24 25 26
		f 3 30 31 -30
		mu 0 3 26 27 24
		f 3 32 33 34
		mu 0 3 28 29 30
		f 3 35 36 -35
		mu 0 3 30 31 28
		f 3 37 38 39
		mu 0 3 32 33 34
		f 3 40 41 -40
		mu 0 3 34 35 32
		f 3 42 43 44
		mu 0 3 36 37 38
		f 3 45 46 -45
		mu 0 3 38 39 36
		f 3 47 48 49
		mu 0 3 40 41 42
		f 3 50 51 -50
		mu 0 3 42 43 40
		f 3 52 53 54
		mu 0 3 44 45 46
		f 3 55 -53 56
		mu 0 3 47 45 44
		f 3 57 58 -56
		mu 0 3 47 48 45
		f 3 59 60 61
		mu 0 3 49 50 51
		f 3 62 -60 63
		mu 0 3 52 50 49
		f 3 64 65 -63
		mu 0 3 52 53 50;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_19_SINGLE";
	rename -uid "52383D21-4A68-0BD1-270C-D8A2E9998958";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_19_SINGLEShape" -p "Joint_1_Object_19_SINGLE";
	rename -uid "DD789EE2-48EA-8EB9-467A-D890DEC678C6";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_19_SINGLEShapeOrig" -p "Joint_1_Object_19_SINGLE";
	rename -uid "08E2D5D5-4B42-4FFD-9935-54B548371B18";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 3 ".uvst[0].uvsp[0:2]" -type "float2" 1.87109005 0.32421899
		 2 1 0 -1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 3 ".vt[0:2]"  3.54152989 6.50680017 -0.98421901 4.2898798 6.31812 -1.86839998
		 1.08051002 7.13079977 -0.087258004;
	setAttr -s 3 ".ed[0:2]"  0 1 0 1 2 0 2 0 0;
	setAttr -s 3 ".n[0:2]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20;
	setAttr -ch 3 ".fc[0]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_20_SINGLE";
	rename -uid "3D6D7D16-4676-DB45-186A-C4A9A6B09B32";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_20_SINGLEShape" -p "Joint_1_Object_20_SINGLE";
	rename -uid "DC66F02B-4524-0B65-0B4C-2EA27BE0C8BB";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_20_SINGLEShapeOrig" -p "Joint_1_Object_20_SINGLE";
	rename -uid "16E85325-4F28-D0CD-6817-E5BD9827FD45";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 3 ".uvst[0].uvsp[0:2]" -type "float2" 0 -1 2 1 1.86719
		 0.32421899;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 3 ".vt[0:2]"  -0.38334599 8.47998047 -1.35354996 0.93076098 9.41407967 -4.77415991
		 0.308438 9.48661041 -3.78096008;
	setAttr -s 3 ".ed[0:2]"  0 1 0 1 2 0 2 0 0;
	setAttr -s 3 ".n[0:2]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20;
	setAttr -ch 3 ".fc[0]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_21_SINGLE";
	rename -uid "84024FB5-4004-E13C-1BC1-7DB3062FB481";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_21_SINGLEShape" -p "Joint_1_Object_21_SINGLE";
	rename -uid "5518D41E-456D-7EAF-9B04-C88373072895";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_21_SINGLEShapeOrig" -p "Joint_1_Object_21_SINGLE";
	rename -uid "FDF34BDD-44C2-9ABC-7085-498605A11272";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0.17968801 -0.953125
		 0.17968801 -1 0.125 -0.90234399 0.875 -0.90234399 0.82031298 -1 0.82031298 -0.953125
		 0.5 -0.89843798 0.82031298 -1 0.875 -0.90234399 0.5 1 0.5 -0.89843798 0.5 1 0.125
		 -0.90234399 0.17968801 -1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 14 ".vt[0:13]"  1.75571001 8.20191002 -3.68590999 1.83144999 8.38465023 -3.58606005
		 1.78416002 8.47132015 -3.73018003 3.15592003 7.20701981 -2.54355001 3.0093300343 7.29905987 -2.56715989
		 2.92873001 7.12079 -2.67121005 2.91946006 8.63626957 -2.80712008 3.0093300343 7.29905987 -2.56715989
		 3.15592003 7.20701981 -2.54355001 4.37049007 9.44521046 -3.62265992 2.91946006 8.63626957 -2.80712008
		 4.37049007 9.44521046 -3.62265992 1.78416002 8.47132015 -3.73018003 1.83144999 8.38465023 -3.58606005;
	setAttr -s 16 ".ed[0:15]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 1 8 9 0 9 6 0 10 11 0 11 12 0 12 10 1 12 13 0 13 10 0;
	setAttr -s 14 ".n[0:13]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 6 -ch 18 ".fc[0:5]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 -9
		mu 0 3 8 9 6
		f 3 11 12 13
		mu 0 3 10 11 12
		f 3 14 15 -14
		mu 0 3 12 13 10;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_22_SINGLE";
	rename -uid "4A9AECFF-4E7D-22F3-5F2B-6FA14DCA6AF3";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_22_SINGLEShape" -p "Joint_1_Object_22_SINGLE";
	rename -uid "967A6A38-43AA-A1D8-83C8-7A8A06A0094F";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".ccls" -type "string" "colorSet0";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_22_SINGLEShapeOrig" -p "Joint_1_Object_22_SINGLE";
	rename -uid "0F90A385-42E9-BDC4-FD63-549CC65763AF";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 5 ".uvst[0].uvsp[0:4]" -type "float2" 3.98828006 1 0 0.26171899
		 0.011718 1 4 0.26171899 2 -3;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr -s 9 ".clst[0].clsp[0:8]"  0.321569 0.33333299 0.321569 1
		 0.321569 0.33333299 0.321569 1 0.321569 0.33333299 0.321569 1 0.321569 0.33333299
		 0.321569 1 0.321569 0.33333299 0.321569 1 0.321569 0.33333299 0.321569 1 0.321569
		 0.33333299 0.321569 1 0.321569 0.33333299 0.321569 1 0.321569 0.33333299 0.321569
		 1;
	setAttr -s 5 ".vt[0:4]"  2.92873001 7.12079 -2.67121005 1.83144999 8.38465023 -3.58606005
		 1.75571001 8.20191002 -3.68590999 3.0093300343 7.29905987 -2.56715989 2.91946006 8.63626957 -2.80712008;
	setAttr -s 7 ".ed[0:6]"  0 1 1 1 2 0 2 0 0 3 1 1 0 3 0 3 4 0 4 1 0;
	setAttr -s 5 ".n[0:4]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 3 -ch 9 ".fc[0:2]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		mc 0 3 0 2 5
		f 3 3 -1 4
		mu 0 3 3 1 0
		mc 0 3 6 3 1
		f 3 5 6 -4
		mu 0 3 3 4 1
		mc 0 3 7 8 4;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_23_SINGLE";
	rename -uid "825E7FBA-4F5C-1360-EE8C-FE825E299E2D";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_23_SINGLEShape" -p "Joint_1_Object_23_SINGLE";
	rename -uid "4928A611-4364-CD24-683E-34B6370FE2B2";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_23_SINGLEShapeOrig" -p "Joint_1_Object_23_SINGLE";
	rename -uid "57B9D7A4-4E1B-18BC-EADA-8B9592B6ACBE";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 8 ".uvst[0].uvsp[0:7]" -type "float2" 1 0.984375 0.13281301
		 0.97656298 0 0.48046899 0.8125 0.75 0 0.48046899 0.13281301 0.97656298 1 0.984375
		 0.8125 0.75;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 8 ".vt[0:7]"  4.79851007 9.73875999 -3.8046999 2.074150085 8.6509304 -3.99048996
		 1.78416002 8.47132015 -3.73018003 4.37049007 9.44521046 -3.62265992 3.15592003 7.20701981 -2.54355001
		 3.52345991 7.3151598 -2.73677993 4.79851007 9.73875999 -3.8046999 4.37049007 9.44521046 -3.62265992;
	setAttr -s 10 ".ed[0:9]"  0 1 0 1 2 0 2 0 1 2 3 0 3 0 0 4 5 0 5 6 0
		 6 4 1 6 7 0 7 4 0;
	setAttr -s 8 ".n[0:7]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 4 -ch 12 ".fc[0:3]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 -3
		mu 0 3 2 3 0
		f 3 5 6 7
		mu 0 3 4 5 6
		f 3 8 9 -8
		mu 0 3 6 7 4;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_24_SINGLE";
	rename -uid "57C0E94E-4D00-27CE-D61F-1F9D11FE0A46";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_24_SINGLEShape" -p "Joint_1_Object_24_SINGLE";
	rename -uid "1B253072-4D84-1305-98BC-B0A8FC518F3C";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_24_SINGLEShapeOrig" -p "Joint_1_Object_24_SINGLE";
	rename -uid "4CAE3251-4831-343C-D69A-02A1B185B6E8";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 6 ".uvst[0].uvsp[0:5]" -type "float2" 0.29296899 0.33984399
		 0.74218798 0 0.74218798 0.33984399 0.74218798 0.33984399 0.74218798 0 0.29296899
		 0.33984399;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 6 ".vt[0:5]"  3.15592003 7.20701981 -2.54355001 3.47811007 6.89187002 -2.73503995
		 3.52345991 7.3151598 -2.73677993 2.074150085 8.6509304 -3.99048996 1.7622 8.47336006 -4.21935987
		 1.78416002 8.47132015 -3.73018003;
	setAttr -s 6 ".ed[0:5]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0;
	setAttr -s 6 ".n[0:5]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 2 -ch 6 ".fc[0:1]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_25_SINGLE";
	rename -uid "74D97FF3-4B27-7EAB-35F6-0D8B2D57A1F6";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_25_SINGLEShape" -p "Joint_1_Object_25_SINGLE";
	rename -uid "4A647BCF-4044-126D-5EAB-97B5F9BB1438";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_25_SINGLEShapeOrig" -p "Joint_1_Object_25_SINGLE";
	rename -uid "1AF001CC-497E-4AF5-513C-F08F32B460D4";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 6 ".uvst[0].uvsp[0:5]" -type "float2" 0.066405997 0.027342999
		 0.77734399 0.035156 0.167969 1.027340055 0.167969 1.027340055 0.77734399 0.035156
		 0.066405997 0.027342999;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 6 ".vt[0:5]"  1.78416002 8.47132015 -3.73018003 1.7622 8.47336006 -4.21935987
		 1.75571001 8.20191002 -3.68590999 2.92873001 7.12079 -2.67121005 3.47811007 6.89187002 -2.73503995
		 3.15592003 7.20701981 -2.54355001;
	setAttr -s 6 ".ed[0:5]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0;
	setAttr -s 6 ".n[0:5]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 2 -ch 6 ".fc[0:1]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_26_SINGLE";
	rename -uid "DCC71B50-43C0-DC65-202F-8FBB6A961FCB";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_26_SINGLEShape" -p "Joint_1_Object_26_SINGLE";
	rename -uid "A4C19334-4B44-EFAA-F273-1483325510C5";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_26_SINGLEShapeOrig" -p "Joint_1_Object_26_SINGLE";
	rename -uid "05BEECD0-4296-CE19-5209-AD8570DC28E0";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 3 ".uvst[0].uvsp[0:2]" -type "float2" 0 0 0 0 0 0;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 3 ".vt[0:2]"  2.8756001 4.79236984 -1.45151997 0.71922898 6.33010006 -0.435388
		 0.65691602 6.37518978 -0.40264499;
	setAttr -s 3 ".ed[0:2]"  0 1 0 1 2 0 2 0 0;
	setAttr -s 3 ".n[0:2]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20;
	setAttr -ch 3 ".fc[0]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_27_SINGLE";
	rename -uid "36575790-437F-5AF8-40D2-6F9E42A5073A";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_27_SINGLEShape" -p "Joint_1_Object_27_SINGLE";
	rename -uid "F6062783-4576-A0E3-2A85-A89C80F14437";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_27_SINGLEShapeOrig" -p "Joint_1_Object_27_SINGLE";
	rename -uid "FED7CF2F-4BAA-FB67-5DED-878C4631A78F";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 4 ".uvst[0].uvsp[0:3]" -type "float2" 0 0 1 1 0 1 1 0;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 4 ".vt[0:3]"  -2.79279995 7.21478987 2.65302992 0.231978 7.44031 -1.94986999
		 0.881504 6.84167004 -1.38800001 -3.040009975 7.44262981 2.4391799;
	setAttr -s 5 ".ed[0:4]"  0 1 1 1 2 0 2 0 0 3 1 0 0 3 0;
	setAttr -s 4 ".n[0:3]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 2 -ch 6 ".fc[0:1]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 -1 4
		mu 0 3 3 1 0;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_28_SINGLE";
	rename -uid "8AE67D6F-4D45-C482-1BFF-96ADA23CF4AB";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_28_SINGLEShape" -p "Joint_1_Object_28_SINGLE";
	rename -uid "46430B30-40E3-87A4-3D47-24BFA686ACF6";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_28_SINGLEShapeOrig" -p "Joint_1_Object_28_SINGLE";
	rename -uid "319D3483-4A54-C2F4-2283-F29EE1B8A156";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 13 ".uvst[0].uvsp[0:12]" -type "float2" 2.92578006 0.28125
		 2.76171994 0.30859399 2.98828006 0.207031 2.76171994 0.69140601 2.92578006 0.71875
		 2.98828006 0.79296899 2.10546994 0.92578101 2.34375 0.69140601 0.87890601 0.57031298
		 0 0.5 0.87890601 0.42968801 2.10546994 0.074217997 2.34375 0.30859399;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 13 ".vt[0:12]"  1.56637001 7.41234016 -3.67509007 1.23246002 7.38622999 -3.16406012
		 1.57202995 7.48508978 -3.98258996 1.88198996 6.78759003 -2.60220003 2.3176899 6.7198801 -3.025170088
		 2.57540989 6.5603199 -3.11464 0.65691602 6.37518978 -0.40264499 0.881504 6.84167004 -1.38800001
		 -2.79279995 7.21478987 2.65302992 -5.019040108 7.40607023 5.059219837 -3.040009975 7.44262981 2.4391799
		 -0.80694199 7.72437 -1.66893005 0.231978 7.44031 -1.94986999;
	setAttr -s 26 ".ed[0:25]"  0 1 1 1 2 1 2 0 0 0 3 1 3 1 0 4 3 1 0 4 0
		 5 3 1 4 5 0 6 3 1 5 6 0 6 7 1 7 3 0 6 8 1 8 7 0 9 8 1 6 9 0 9 10 1 10 8 0 11 10 1
		 9 11 0 2 12 1 12 11 1 11 2 0 1 12 0 12 10 0;
	setAttr -s 13 ".n[0:12]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 13 -ch 39 ".fc[0:12]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 -1
		mu 0 3 0 3 1
		f 3 5 -4 6
		mu 0 3 4 3 0
		f 3 7 -6 8
		mu 0 3 5 3 4
		f 3 9 -8 10
		mu 0 3 6 3 5
		f 3 11 12 -10
		mu 0 3 6 7 3
		f 3 13 14 -12
		mu 0 3 6 8 7
		f 3 15 -14 16
		mu 0 3 9 8 6
		f 3 17 18 -16
		mu 0 3 9 10 8
		f 3 19 -18 20
		mu 0 3 11 10 9
		f 3 21 22 23
		mu 0 3 2 12 11
		f 3 -2 24 -22
		mu 0 3 2 1 12
		f 3 -23 25 -20
		mu 0 3 11 12 10;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_29_SINGLE";
	rename -uid "3DA26708-44B9-52A7-4A40-0EAE1E078F00";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_29_SINGLEShape" -p "Joint_1_Object_29_SINGLE";
	rename -uid "7729BF40-4A92-9E27-B3BE-6689CA84ED94";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_29_SINGLEShapeOrig" -p "Joint_1_Object_29_SINGLE";
	rename -uid "4D0D3ECA-4619-346C-C29F-0C91D0E1E6BB";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 18 ".uvst[0].uvsp[0:17]" -type "float2" 0.90625 -1 0 1 1
		 0.984375 1 0.984375 0 1 0.90625 -1 0.90234399 -1 0 1 1 0.99609399 1 0.984375 0 1
		 1 0.984375 1 0.99218798 0 1 0.90234399 -1 1 0.99609399 0 1 1 0.99218798;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 18 ".vt[0:17]"  -0.73462802 8.15423012 -4.65706015 -5.4391799 9.41625977 -6.79692984
		 -0.073494002 8.31262016 -5.45637989 -0.229651 8.034070015 -5.57263994 -5.4391799 9.41625977 -6.79692984
		 -0.73462802 8.15423012 -4.65706015 2.93712997 4.77011013 -1.48084998 4.23342991 0.50141197 1.57023001
		 3.57540989 4.52710009 -2.28113008 -0.073494002 8.31262016 -5.45637989 -5.4391799 9.41625977 -6.79692984
		 -0.229651 8.034070015 -5.57263994 3.72914004 4.80788994 -2.16696 4.23342991 0.50141197 1.57023001
		 2.93712997 4.77011013 -1.48084998 3.57540989 4.52710009 -2.28113008 4.23342991 0.50141197 1.57023001
		 3.72914004 4.80788994 -2.16696;
	setAttr -s 18 ".ed[0:17]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 0 9 10 0 10 11 0 11 9 0 12 13 0 13 14 0 14 12 0 15 16 0 16 17 0 17 15 0;
	setAttr -s 18 ".n[0:17]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 6 -ch 18 ".fc[0:5]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 11
		mu 0 3 9 10 11
		f 3 12 13 14
		mu 0 3 12 13 14
		f 3 15 16 17
		mu 0 3 15 16 17;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_30_SINGLE";
	rename -uid "CBE5EE2F-466D-3D0D-3A27-67B2D4617F16";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_30_SINGLEShape" -p "Joint_1_Object_30_SINGLE";
	rename -uid "6468CCDC-424D-158D-359F-E699A6B0B0EB";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_30_SINGLEShapeOrig" -p "Joint_1_Object_30_SINGLE";
	rename -uid "ADB104B0-4567-4DD5-3AA9-37B0DA03B2EE";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 3 ".uvst[0].uvsp[0:2]" -type "float2" 0.82031298 0.53125
		 0.82031298 0.222656 0 0.38671899;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 3 ".vt[0:2]"  0.84767401 6.11048985 -2.59372997 0.50836903 6.42322016 -2.88723993
		 -5.20110989 7.39612007 5.25908995;
	setAttr -s 3 ".ed[0:2]"  0 1 0 1 2 0 2 0 0;
	setAttr -s 3 ".n[0:2]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20;
	setAttr -ch 3 ".fc[0]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_31_SINGLE";
	rename -uid "90D4B550-40C4-8EC8-CBC1-EB848329B1AE";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_31_SINGLEShape" -p "Joint_1_Object_31_SINGLE";
	rename -uid "0AD33D65-40DD-99D7-90A6-D7B2E1CFD3C7";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_31_SINGLEShapeOrig" -p "Joint_1_Object_31_SINGLE";
	rename -uid "287D7924-4D38-8D8C-5677-B4A86F2B61F8";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 72 ".uvst[0].uvsp[0:71]" -type "float2" 0.49609399 1 0.56640601
		 -0.41406301 0.42968801 -0.41406301 1 1 0.98046899 0.29296899 0.94140601 0.296875
		 0 1 0.78125 -1 0.94140601 0.921875 0.78515601 -1 0.765625 -0.96093798 0.042968001
		 0.32421899 1 1 0.64843798 1 0 0.46875 0.94140601 0.921875 0.78515601 -1 0 1 0.56640601
		 -0.41406301 0.71875 -1 0.27734399 -1 0.42968801 -0.41406301 0.171875 0.5 0 0 1 0.5
		 0 1 0 0.52734399 1 0 0.9375 0.105469 0.050781 0.52734399 1 1 0 0.52734399 0.050781
		 0.52734399 0.9375 0.89843798 1 0 1 1 0.9375 0.89843798 0.9375 0.105469 1 1 1 0 0.9375
		 0.105469 0.9375 0.89843798 0 0.52734399 1 1 0.9375 0.89843798 0.050781 0.52734399
		 1 0 0 0.52734399 0.050781 0.52734399 0.9375 0.105469 0.98046899 0.29296899 0.0625
		 0 0.0078119999 0.0078119999 0.94140601 0.296875 0.94140601 0.296875 0.0078119999
		 0.0078119999 0.0625 0 0.98046899 0.29296899 0.76171899 -0.96093798 0.042968001 0.32421899
		 0 1 1 0.91796899 1 0.91796899 0 1 0.042968001 0.32421899 0.765625 -0.96093798 0.94140601
		 0.296875 0.98046899 0.29296899 0.0078119999 0.0078119999 0 0.46875 0.64843798 1 0.0078119999
		 0.0078119999;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 72 ".vt[0:71]"  3.011450052 5.081830025 -6.70057011 0.91753799 5.26225996 -4.24057007
		 1.019330025 5.16843987 -4.15252018 3.011450052 5.081830025 -6.70057011 1.019330025 5.16843987 -4.15252018
		 1.079429984 5.19124985 -4.13946009 3.77113008 4.86623001 -2.22612 0.65691602 6.37518978 -0.40264499
		 2.57540989 6.5603199 -3.11464 -0.80694199 7.72437 -1.66893005 -0.80279601 7.73288012 -1.75198996
		 -0.75011402 8.13403988 -4.58789015 3.011450052 5.081830025 -6.70057011 3.22864008 5.46924019 -6.53886986
		 1.84783995 6.48016977 -4.57153988 1.57202995 7.48508978 -3.98258996 -0.80694199 7.72437 -1.66893005
		 0.01939 8.32404995 -5.47150993 0.91753799 5.26225996 -4.24057007 0.50836903 6.42322016 -2.88723993
		 0.84767401 6.11048985 -2.59372997 1.019330025 5.16843987 -4.15252018 2.27856994 6.12426996 -4.74267006
		 1.84783995 6.48016977 -4.57153988 3.22864008 5.46924019 -6.53886986 2.31802011 6.046820164 -4.16481018
		 -0.75011402 8.13403988 -4.58789015 -0.17742001 7.96643019 -5.61775017 -0.229651 8.034070015 -5.57263994
		 -0.73462802 8.15423012 -4.65706015 0.01939 8.32404995 -5.47150993 -0.75011402 8.13403988 -4.58789015
		 -0.73462802 8.15423012 -4.65706015 -0.073494002 8.31262016 -5.45637989 -0.17742001 7.96643019 -5.61775017
		 0.01939 8.32404995 -5.47150993 -0.073494002 8.31262016 -5.45637989 -0.229651 8.034070015 -5.57263994
		 3.77113008 4.86623001 -2.22612 3.57189989 4.51082993 -2.37445998 3.57540989 4.52710009 -2.28113008
		 3.72914004 4.80788994 -2.16696 2.8756001 4.79236984 -1.45151997 3.77113008 4.86623001 -2.22612
		 3.72914004 4.80788994 -2.16696 2.93712997 4.77011013 -1.48084998 3.57189989 4.51082993 -2.37445998
		 2.8756001 4.79236984 -1.45151997 2.93712997 4.77011013 -1.48084998 3.57540989 4.52710009 -2.28113008
		 1.019330025 5.16843987 -4.15252018 0.84767401 6.11048985 -2.59372997 0.96476901 6.11638021 -2.54815006
		 1.079429984 5.19124985 -4.13946009 0.93886101 5.32080984 -4.26106024 0.50913101 6.53632021 -2.94229007
		 0.50836903 6.42322016 -2.88723993 0.91753799 5.26225996 -4.24057007 0.71922898 6.33010006 -0.435388
		 2.8756001 4.79236984 -1.45151997 3.57189989 4.51082993 -2.37445998 2.1798501 6.099909782 -3.40994
		 1.35098004 6.86385012 -4.12693977 -0.17742001 7.96643019 -5.61775017 -0.75011402 8.13403988 -4.58789015
		 -0.80279601 7.73288012 -1.75198996 0.93886101 5.32080984 -4.26106024 0.91753799 5.26225996 -4.24057007
		 0.50913101 6.53632021 -2.94229007 2.31802011 6.046820164 -4.16481018 3.22864008 5.46924019 -6.53886986
		 0.96476901 6.11638021 -2.54815006;
	setAttr -s 90 ".ed[0:89]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 1 6 7 0
		 7 8 0 8 6 0 9 10 0 10 11 0 11 9 0 12 13 0 13 14 0 14 12 1 15 16 0 16 17 0 17 15 0
		 18 19 0 19 20 0 20 18 1 20 21 0 21 18 0 22 23 0 23 24 0 24 22 1 24 25 0 25 22 0 26 27 0
		 27 28 0 28 26 1 28 29 0 29 26 0 30 31 0 31 32 0 32 30 1 32 33 0 33 30 0 34 35 0 35 36 0
		 36 34 1 36 37 0 37 34 0 38 39 0 39 40 0 40 38 1 40 41 0 41 38 0 42 43 0 43 44 0 44 42 1
		 44 45 0 45 42 0 46 47 0 47 48 0 48 46 1 48 49 0 49 46 0 50 51 0 51 52 0 52 50 1 52 53 0
		 53 50 0 54 55 0 55 56 0 56 54 1 56 57 0 57 54 0 58 59 0 59 60 0 60 58 1 60 61 0 61 58 0
		 62 63 0 63 64 0 64 62 1 64 65 0 65 62 0 14 66 1 66 12 1 66 67 0 67 12 0 14 68 0 68 66 0
		 5 69 1 69 3 1 69 70 0 70 3 0 5 71 0 71 69 0;
	setAttr -s 72 ".n[0:71]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20;
	setAttr -s 36 -ch 108 ".fc[0:35]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 11
		mu 0 3 9 10 11
		f 3 12 13 14
		mu 0 3 12 13 14
		f 3 15 16 17
		mu 0 3 15 16 17
		f 3 18 19 20
		mu 0 3 18 19 20
		f 3 21 22 -21
		mu 0 3 20 21 18
		f 3 23 24 25
		mu 0 3 22 23 24
		f 3 26 27 -26
		mu 0 3 24 25 22
		f 3 28 29 30
		mu 0 3 26 27 28
		f 3 31 32 -31
		mu 0 3 28 29 26
		f 3 33 34 35
		mu 0 3 30 31 32
		f 3 36 37 -36
		mu 0 3 32 33 30
		f 3 38 39 40
		mu 0 3 34 35 36
		f 3 41 42 -41
		mu 0 3 36 37 34
		f 3 43 44 45
		mu 0 3 38 39 40
		f 3 46 47 -46
		mu 0 3 40 41 38
		f 3 48 49 50
		mu 0 3 42 43 44
		f 3 51 52 -51
		mu 0 3 44 45 42
		f 3 53 54 55
		mu 0 3 46 47 48
		f 3 56 57 -56
		mu 0 3 48 49 46
		f 3 58 59 60
		mu 0 3 50 51 52
		f 3 61 62 -61
		mu 0 3 52 53 50
		f 3 63 64 65
		mu 0 3 54 55 56
		f 3 66 67 -66
		mu 0 3 56 57 54
		f 3 68 69 70
		mu 0 3 58 59 60
		f 3 71 72 -71
		mu 0 3 60 61 58
		f 3 73 74 75
		mu 0 3 62 63 64
		f 3 76 77 -76
		mu 0 3 64 65 62
		f 3 78 79 -15
		mu 0 3 14 66 12
		f 3 -80 80 81
		mu 0 3 12 66 67
		f 3 82 83 -79
		mu 0 3 14 68 66
		f 3 84 85 -6
		mu 0 3 5 69 3
		f 3 -86 86 87
		mu 0 3 3 69 70
		f 3 88 89 -85
		mu 0 3 5 71 69;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_32_SINGLE";
	rename -uid "E1E0F1BD-4E8F-7194-40DB-C0A203799552";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_32_SINGLEShape" -p "Joint_1_Object_32_SINGLE";
	rename -uid "274652D7-4850-3447-F1E4-B5A9F00A5A44";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_32_SINGLEShapeOrig" -p "Joint_1_Object_32_SINGLE";
	rename -uid "4C7BEB9E-48C8-9F62-C262-1BA3873F0653";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 6 ".uvst[0].uvsp[0:5]" -type "float2" 0 -1 2 1 1.89063001
		 0.32421899 1.88671994 0.32421899 2 1 0 -1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 6 ".vt[0:5]"  0.65691602 6.37518978 -0.40264499 3.77113008 4.86623001 -2.22612
		 2.8756001 4.79236984 -1.45151997 -0.75011402 8.13403988 -4.58789015 0.01939 8.32404995 -5.47150993
		 -0.80694199 7.72437 -1.66893005;
	setAttr -s 6 ".ed[0:5]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0;
	setAttr -s 6 ".n[0:5]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 2 -ch 6 ".fc[0:1]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_33_SINGLE";
	rename -uid "1319EE53-44CD-CD33-44F9-3FA6175EAE42";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_33_SINGLEShape" -p "Joint_1_Object_33_SINGLE";
	rename -uid "C4F9A1A7-46EB-8839-D922-01ADE87EA7D2";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_33_SINGLEShapeOrig" -p "Joint_1_Object_33_SINGLE";
	rename -uid "A98C2895-4B4C-7913-7BF7-04854F4D982D";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 8 ".uvst[0].uvsp[0:7]" -type "float2" 1 0 1 1 0 0.953125
		 0.039062001 0.31640601 1 0 0.035156 0.30859399 0 0.94531298 1 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 8 ".vt[0:7]"  2.57540989 6.5603199 -3.11464 2.1798501 6.099909782 -3.40994
		 3.57189989 4.51082993 -2.37445998 3.77113008 4.86623001 -2.22612 1.57202995 7.48508978 -3.98258996
		 0.01939 8.32404995 -5.47150993 -0.17742001 7.96643019 -5.61775017 1.35098004 6.86385012 -4.12693977;
	setAttr -s 10 ".ed[0:9]"  0 1 0 1 2 0 2 0 1 2 3 0 3 0 0 4 5 0 5 6 0
		 6 4 1 6 7 0 7 4 0;
	setAttr -s 8 ".n[0:7]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 4 -ch 12 ".fc[0:3]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 -3
		mu 0 3 2 3 0
		f 3 5 6 7
		mu 0 3 4 5 6
		f 3 8 9 -8
		mu 0 3 6 7 4;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_34_SINGLE";
	rename -uid "3D9F08FB-4030-7C87-A256-BE90FF7A55B9";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_34_SINGLEShape" -p "Joint_1_Object_34_SINGLE";
	rename -uid "973AB9D3-4692-5336-1FC1-BFB9CEE55299";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_34_SINGLEShapeOrig" -p "Joint_1_Object_34_SINGLE";
	rename -uid "494BBF44-4C7C-20D6-A6F4-8D8A7B95B0B2";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 25 ".uvst[0].uvsp[0:24]" -type "float2" 0.94531298 0.95703101
		 1 0.082030997 0.94531298 0.31640601 0.94531298 0.31640601 1 0.082030997 0.94531298
		 0.95703101 0.67578101 0.83593798 0.671875 0.85546899 0.023437001 0.95703101 0 0.9375
		 0.67578101 0.83593798 0 0.9375 0.671875 0.85546899 0.94531298 0.31640601 0.82421899
		 0.074217997 1 0.082030997 0.67578101 0.83593798 0 0.9375 0.82421899 0 0 0.9375 0.82421899
		 0.074217997 0.82421899 0 0.67578101 0.83593798 0.94531298 0.31640601 1 0.082030997;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 25 ".vt[0:24]"  2.57540989 6.5603199 -3.11464 2.31802011 6.046820164 -4.16481018
		 2.1798501 6.099909782 -3.40994 1.35098004 6.86385012 -4.12693977 1.84783995 6.48016977 -4.57153988
		 1.57202995 7.48508978 -3.98258996 -0.80279601 7.73288012 -1.75198996 -0.80694199 7.72437 -1.66893005
		 -5.019040108 7.40607023 5.059219837 -5.20110989 7.39612007 5.25908995 0.71922898 6.33010006 -0.435388
		 -5.20110989 7.39612007 5.25908995 0.65691602 6.37518978 -0.40264499 1.35098004 6.86385012 -4.12693977
		 0.50913101 6.53632021 -2.94229007 1.84783995 6.48016977 -4.57153988 -0.80279601 7.73288012 -1.75198996
		 -5.20110989 7.39612007 5.25908995 0.50836903 6.42322016 -2.88723993 -5.20110989 7.39612007 5.25908995
		 0.96476901 6.11638021 -2.54815006 0.84767401 6.11048985 -2.59372997 0.71922898 6.33010006 -0.435388
		 2.1798501 6.099909782 -3.40994 2.31802011 6.046820164 -4.16481018;
	setAttr -s 34 ".ed[0:33]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 1 8 9 0 9 6 0 10 11 0 11 8 0 8 10 1 8 12 0 12 10 0 13 14 1 14 15 0 15 13 0
		 16 14 1 13 16 0 17 14 1 16 17 0 17 18 0 18 14 0 19 20 1 20 21 0 21 19 0 22 20 1 19 22 0
		 23 20 1 22 23 0 23 24 0 24 20 0;
	setAttr -s 26 ".n[0:25]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20;
	setAttr -s 14 -ch 42 ".fc[0:13]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 -9
		mu 0 3 8 9 6
		f 3 11 12 13
		mu 0 3 10 11 8
		f 3 14 15 -14
		mu 0 3 8 12 10
		f 3 16 17 18
		mu 0 3 13 14 15
		f 3 19 -17 20
		mu 0 3 16 14 13
		f 3 21 -20 22
		mu 0 3 17 14 16
		f 3 23 24 -22
		mu 0 3 17 18 14
		f 3 25 26 27
		mu 0 3 19 20 21
		f 3 28 -26 29
		mu 0 3 22 20 19
		f 3 30 -29 31
		mu 0 3 23 20 22
		f 3 32 33 -31
		mu 0 3 23 24 20;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_35_SINGLE";
	rename -uid "2CD15C01-483A-A684-B28C-56A0C3E38546";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_35_SINGLEShape" -p "Joint_1_Object_35_SINGLE";
	rename -uid "AF59480D-431A-0842-A05C-889FFCFA4FD8";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_35_SINGLEShapeOrig" -p "Joint_1_Object_35_SINGLE";
	rename -uid "B78A43BE-4BC3-F482-7E30-8D93C7A2F33C";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 10 ".uvst[0].uvsp[0:9]" -type "float2" 0.81640601 0.36718801
		 0.5 -1 1 -0.98828101 0 -0.98828101 0.5 -1 0.183594 0.36718801 0.5 1 0.5 -1 0.81640601
		 0.36718801 0.183594 0.36718801;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 10 ".vt[0:9]"  1.84783995 6.48016977 -4.57153988 1.65415001 6.55716991 -3.55960011
		 1.47737002 7.25101995 -3.75136995 2.23353004 6.55409002 -3.097249985 1.65415001 6.55716991 -3.55960011
		 2.31802011 6.046820164 -4.16481018 2.27856994 6.12426996 -4.74267006 1.65415001 6.55716991 -3.55960011
		 1.84783995 6.48016977 -4.57153988 2.31802011 6.046820164 -4.16481018;
	setAttr -s 11 ".ed[0:10]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 1
		 7 8 0 8 6 0 9 7 0 6 9 0;
	setAttr -s 10 ".n[0:9]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 4 -ch 12 ".fc[0:3]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 -7 10
		mu 0 3 9 7 6;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_36_SINGLE";
	rename -uid "03D39105-4A48-DAEA-47B4-7E8EC02619C9";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_36_SINGLEShape" -p "Joint_1_Object_36_SINGLE";
	rename -uid "293293C0-4CE3-58B4-6504-B9BB0943437A";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_36_SINGLEShapeOrig" -p "Joint_1_Object_36_SINGLE";
	rename -uid "1BE273E7-4DED-91D9-2504-9498D574E322";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 5 ".uvst[0].uvsp[0:4]" -type "float2" 1.99219 1 0 0.359375
		 0.0078119999 1 2 0.359375 1 -1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 5 ".vt[0:4]"  1.56637001 7.41234016 -3.67509007 2.23353004 6.55409002 -3.097249985
		 2.3176899 6.7198801 -3.025170088 1.47737002 7.25101995 -3.75136995 1.65415001 6.55716991 -3.55960011;
	setAttr -s 7 ".ed[0:6]"  0 1 1 1 2 0 2 0 0 3 1 1 0 3 0 3 4 0 4 1 0;
	setAttr -s 5 ".n[0:4]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 3 -ch 9 ".fc[0:2]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 -1 4
		mu 0 3 3 1 0
		f 3 5 6 -4
		mu 0 3 3 4 1;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_37_SINGLE";
	rename -uid "5134DFB2-4F6F-B0ED-2F1B-5C8574D40A7A";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_37_SINGLEShape" -p "Joint_1_Object_37_SINGLE";
	rename -uid "1F58C905-4630-DC59-27A3-FF811FCD352F";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_37_SINGLEShapeOrig" -p "Joint_1_Object_37_SINGLE";
	rename -uid "3B413E39-4220-3DBA-EF9B-009657137591";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 12 ".uvst[0].uvsp[0:11]" -type "float2" 0.16406301 0.94140601
		 1 0.058593001 0.101563 0.070312001 0.16406301 0.94140601 0.101563 0.070312001 1 0.058593001
		 0.16406301 0.94140601 0.101563 0.070312001 0 0.55859399 0 0.55859399 0.101563 0.070312001
		 0.16406301 0.94140601;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 12 ".vt[0:11]"  1.57202995 7.48508978 -3.98258996 1.84783995 6.48016977 -4.57153988
		 1.47737002 7.25101995 -3.75136995 2.57540989 6.5603199 -3.11464 2.23353004 6.55409002 -3.097249985
		 2.31802011 6.046820164 -4.16481018 1.57202995 7.48508978 -3.98258996 1.47737002 7.25101995 -3.75136995
		 1.56637001 7.41234016 -3.67509007 2.3176899 6.7198801 -3.025170088 2.23353004 6.55409002 -3.097249985
		 2.57540989 6.5603199 -3.11464;
	setAttr -s 12 ".ed[0:11]"  0 1 0 1 2 0 2 0 0 3 4 0 4 5 0 5 3 0 6 7 0
		 7 8 0 8 6 0 9 10 0 10 11 0 11 9 0;
	setAttr -s 12 ".n[0:11]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20;
	setAttr -s 4 -ch 12 ".fc[0:3]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 5
		mu 0 3 3 4 5
		f 3 6 7 8
		mu 0 3 6 7 8
		f 3 9 10 11
		mu 0 3 9 10 11;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_38_SINGLE";
	rename -uid "67906F9F-46DF-06E8-1ED3-57938455A9A5";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_38_SINGLEShape" -p "Joint_1_Object_38_SINGLE";
	rename -uid "10C50831-415D-884A-4133-4891C03793BF";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".ccls" -type "string" "colorSet0";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_38_SINGLEShapeOrig" -p "Joint_1_Object_38_SINGLE";
	rename -uid "BFBBD4B5-465F-90B7-897E-2984A2D3D02C";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 13 0 11 0.68359399
		 13 0.68359399 11 0 9 0.68359399 9 0 7 0.68359399 7 0 5 0.68359399 5 0 3 0.68359399
		 3 0 1 0.68359399 1 0;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr -s 36 ".clst[0].clsp[0:35]"  1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1;
	setAttr -s 14 ".vt[0:13]"  2.85561991 7.21648979 -3.69289994 2.82189012 7.19156981 -2.95990992
		 2.66193008 7.33900023 -3.098279953 3.17553997 6.92163992 -3.41616011 3.00059008598 7.29396009 -2.81722999
		 3.5329299 7.12639999 -3.13079 3.019330025 7.54376984 -2.81291008 3.56861997 7.6228199 -3.1234901
		 2.85936999 7.69118977 -2.95128012 3.2486999 7.91766977 -3.40022993 2.68067002 7.58880997 -3.093960047
		 2.89310002 7.71611023 -3.68426991 2.66193008 7.33900023 -3.098279953 2.85561991 7.21648979 -3.69289994;
	setAttr -s 25 ".ed[0:24]"  0 1 1 1 2 0 2 0 0 3 1 1 0 3 0 3 4 1 4 1 0
		 5 4 1 3 5 0 5 6 1 6 4 0 7 6 1 5 7 0 7 8 1 8 6 0 9 8 1 7 9 0 9 10 1 10 8 0 11 10 1
		 9 11 0 11 12 1 12 10 0 13 12 0 11 13 0;
	setAttr -s 14 ".n[0:13]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 12 -ch 36 ".fc[0:11]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		mc 0 3 0 2 5
		f 3 3 -1 4
		mu 0 3 3 1 0
		mc 0 3 6 3 1
		f 3 5 6 -4
		mu 0 3 3 4 1
		mc 0 3 7 9 4
		f 3 7 -6 8
		mu 0 3 5 4 3
		mc 0 3 12 10 8
		f 3 9 10 -8
		mu 0 3 5 6 4
		mc 0 3 13 15 11
		f 3 11 -10 12
		mu 0 3 7 6 5
		mc 0 3 18 16 14
		f 3 13 14 -12
		mu 0 3 7 8 6
		mc 0 3 19 21 17
		f 3 15 -14 16
		mu 0 3 9 8 7
		mc 0 3 24 22 20
		f 3 17 18 -16
		mu 0 3 9 10 8
		mc 0 3 25 27 23
		f 3 19 -18 20
		mu 0 3 11 10 9
		mc 0 3 30 28 26
		f 3 21 22 -20
		mu 0 3 11 12 10
		mc 0 3 31 33 29
		f 3 23 -22 24
		mu 0 3 13 12 11
		mc 0 3 35 34 32;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_39_SINGLE";
	rename -uid "E3ED472F-472D-FB8B-D953-A38C0C4E20A4";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_39_SINGLEShape" -p "Joint_1_Object_39_SINGLE";
	rename -uid "7BDA5B59-445D-DB28-777C-CF95DA98BEAC";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_39_SINGLEShapeOrig" -p "Joint_1_Object_39_SINGLE";
	rename -uid "60CD73E1-4231-F3B8-D00C-89AFA72DF29A";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 24 ".uvst[0].uvsp[0:23]" -type "float2" 2.33203006 -2 2.33203006
		 1 1.66796994 1 1.66796994 -2 3 -2 3 1 2.33203006 1 2.33203006 -2 1.66796994 -2 1.66796994
		 1 1 1 1 -2 1 -2 1 1 0.33203101 1 0.33203101 -2 3.66796994 -2 3.66796994 1 3 1 3 -2
		 4.33202982 -2 4.33202982 1 3.66796994 1 3.66796994 -2;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 24 ".vt[0:23]"  3.56861997 7.6228199 -3.1234901 2.94122005 7.60580015 -2.52551007
		 2.69402003 7.8336401 -2.73936009 3.2486999 7.91766977 -3.40022993 3.5329299 7.12639999 -3.13079
		 2.91162992 7.22517014 -2.53294992 2.94122005 7.60580015 -2.52551007 3.56861997 7.6228199 -3.1234901
		 3.2486999 7.91766977 -3.40022993 2.69402003 7.8336401 -2.73936009 2.41964006 7.67861986 -2.95853996
		 2.89310002 7.71611023 -3.68426991 2.89310002 7.71611023 -3.68426991 2.41964006 7.67861986 -2.95853996
		 2.39068007 7.29255009 -2.96520996 2.85561991 7.21648979 -3.69289994 3.17553997 6.92163992 -3.41616011
		 2.6378901 7.06471014 -2.75135994 2.91162992 7.22517014 -2.53294992 3.5329299 7.12639999 -3.13079
		 2.85561991 7.21648979 -3.69289994 2.39068007 7.29255009 -2.96520996 2.6378901 7.06471014 -2.75135994
		 3.17553997 6.92163992 -3.41616011;
	setAttr -s 30 ".ed[0:29]"  0 1 0 1 2 0 2 0 1 2 3 0 3 0 0 4 5 0 5 6 0
		 6 4 1 6 7 0 7 4 0 8 9 0 9 10 0 10 8 1 10 11 0 11 8 0 12 13 0 13 14 0 14 12 1 14 15 0
		 15 12 0 16 17 0 17 18 0 18 16 1 18 19 0 19 16 0 20 21 0 21 22 0 22 20 1 22 23 0 23 20 0;
	setAttr -s 24 ".n[0:23]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 12 -ch 36 ".fc[0:11]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 -3
		mu 0 3 2 3 0
		f 3 5 6 7
		mu 0 3 4 5 6
		f 3 8 9 -8
		mu 0 3 6 7 4
		f 3 10 11 12
		mu 0 3 8 9 10
		f 3 13 14 -13
		mu 0 3 10 11 8
		f 3 15 16 17
		mu 0 3 12 13 14
		f 3 18 19 -18
		mu 0 3 14 15 12
		f 3 20 21 22
		mu 0 3 16 17 18
		f 3 23 24 -23
		mu 0 3 18 19 16
		f 3 25 26 27
		mu 0 3 20 21 22
		f 3 28 29 -28
		mu 0 3 22 23 20;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_40_SINGLE";
	rename -uid "215B2E27-4EA0-E812-18F1-2B8EAC76D698";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_40_SINGLEShape" -p "Joint_1_Object_40_SINGLE";
	rename -uid "4915110C-42D4-5065-ECCC-CB8834D330DB";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".ccls" -type "string" "colorSet0";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_40_SINGLEShapeOrig" -p "Joint_1_Object_40_SINGLE";
	rename -uid "4068CFC7-4FF8-78AC-14AB-A191C38B5287";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 6 ".uvst[0].uvsp[0:5]" -type "float2" 0.25 0 1 0.5 0.75
		 0 0 0.5 0.75 1 0.25 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr -s 12 ".clst[0].clsp[0:11]"  1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
	setAttr -s 6 ".vt[0:5]"  2.85936999 7.69118977 -2.95128012 3.00059008598 7.29396009 -2.81722999
		 3.019330025 7.54376984 -2.81291008 2.68067002 7.58880997 -3.093960047 2.82189012 7.19156981 -2.95990992
		 2.66193008 7.33900023 -3.098279953;
	setAttr -s 9 ".ed[0:8]"  0 1 1 1 2 0 2 0 0 3 1 1 0 3 0 3 4 1 4 1 0
		 5 4 0 3 5 0;
	setAttr -s 6 ".n[0:5]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 4 -ch 12 ".fc[0:3]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		mc 0 3 0 2 5
		f 3 3 -1 4
		mu 0 3 3 1 0
		mc 0 3 6 3 1
		f 3 5 6 -4
		mu 0 3 3 4 1
		mc 0 3 7 9 4
		f 3 7 -6 8
		mu 0 3 5 4 3
		mc 0 3 11 10 8;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_41_SINGLE";
	rename -uid "287C1E6B-4048-F2D5-6A13-8595CAE9A1B4";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_41_SINGLEShape" -p "Joint_1_Object_41_SINGLE";
	rename -uid "2056AFC6-4802-0674-DFB0-78A98AFB44C1";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".ccls" -type "string" "colorSet0";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_41_SINGLEShapeOrig" -p "Joint_1_Object_41_SINGLE";
	rename -uid "26ED5510-4B7C-ED2C-F7BB-3F8DC2AE6657";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 13 0 11 0.68359399
		 13 0.68359399 11 0 9 0.68359399 9 0 7 0.68359399 7 0 5 0.68359399 5 0 3 0.68359399
		 3 0 1 0.68359399 1 0;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr -s 36 ".clst[0].clsp[0:35]"  1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1;
	setAttr -s 14 ".vt[0:13]"  2.16732001 7.85087013 -4.28831005 2.13357997 7.82595015 -3.55532002
		 1.97362995 7.97338009 -3.69369006 2.48723006 7.55601978 -4.011569977 2.31227994 7.92833996 -3.41263008
		 2.84463 7.76077986 -3.7262001 2.33102012 8.17815018 -3.40831995 2.88032007 8.25720024 -3.71889997
		 2.1710701 8.32557011 -3.54668999 2.56040001 8.55204964 -3.99564004 1.99237001 8.22319031 -3.68936992
		 2.20479989 8.35048962 -4.27967978 1.97362995 7.97338009 -3.69369006 2.16732001 7.85087013 -4.28831005;
	setAttr -s 25 ".ed[0:24]"  0 1 1 1 2 0 2 0 0 3 1 1 0 3 0 3 4 1 4 1 0
		 5 4 1 3 5 0 5 6 1 6 4 0 7 6 1 5 7 0 7 8 1 8 6 0 9 8 1 7 9 0 9 10 1 10 8 0 11 10 1
		 9 11 0 11 12 1 12 10 0 13 12 0 11 13 0;
	setAttr -s 14 ".n[0:13]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 12 -ch 36 ".fc[0:11]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		mc 0 3 0 2 5
		f 3 3 -1 4
		mu 0 3 3 1 0
		mc 0 3 6 3 1
		f 3 5 6 -4
		mu 0 3 3 4 1
		mc 0 3 7 9 4
		f 3 7 -6 8
		mu 0 3 5 4 3
		mc 0 3 12 10 8
		f 3 9 10 -8
		mu 0 3 5 6 4
		mc 0 3 13 15 11
		f 3 11 -10 12
		mu 0 3 7 6 5
		mc 0 3 18 16 14
		f 3 13 14 -12
		mu 0 3 7 8 6
		mc 0 3 19 21 17
		f 3 15 -14 16
		mu 0 3 9 8 7
		mc 0 3 24 22 20
		f 3 17 18 -16
		mu 0 3 9 10 8
		mc 0 3 25 27 23
		f 3 19 -18 20
		mu 0 3 11 10 9
		mc 0 3 30 28 26
		f 3 21 22 -20
		mu 0 3 11 12 10
		mc 0 3 31 33 29
		f 3 23 -22 24
		mu 0 3 13 12 11
		mc 0 3 35 34 32;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_42_SINGLE";
	rename -uid "13EA222E-4E90-EDCF-A18B-BEAFCC4864C4";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_42_SINGLEShape" -p "Joint_1_Object_42_SINGLE";
	rename -uid "45A75BFD-4CED-DE0A-3F76-5CBCCE6759D8";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_42_SINGLEShapeOrig" -p "Joint_1_Object_42_SINGLE";
	rename -uid "2B1A4880-40D9-265A-723A-EBBF933B15C3";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 24 ".uvst[0].uvsp[0:23]" -type "float2" 2.33203006 -2 2.33203006
		 1 1.66796994 1 1.66796994 -2 3 -2 3 1 2.33203006 1 2.33203006 -2 1.66796994 -2 1.66796994
		 1 1 1 1 -2 1 -2 1 1 0.33203101 1 0.33203101 -2 3.66796994 -2 3.66796994 1 3 1 3 -2
		 4.33202982 -2 4.33202982 1 3.66796994 1 3.66796994 -2;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 24 ".vt[0:23]"  2.88032007 8.25720024 -3.71889997 2.25291991 8.24018002 -3.12091994
		 2.0057098866 8.46802044 -3.33476996 2.56040001 8.55204964 -3.99564004 2.84463 7.76077986 -3.7262001
		 2.22574997 7.85731983 -3.12626004 2.25291991 8.24018002 -3.12091994 2.88032007 8.25720024 -3.71889997
		 2.56040001 8.55204964 -3.99564004 2.0057098866 8.46802044 -3.33476996 1.73376 8.31075954 -3.55185008
		 2.20479989 8.35048962 -4.27967978 2.20479989 8.35048962 -4.27967978 1.73376 8.31075954 -3.55185008
		 1.70237005 7.92692995 -3.56061006 2.16732001 7.85087013 -4.28831005 2.48723006 7.55601978 -4.011569977
		 1.94957995 7.69909 -3.34677005 2.22574997 7.85731983 -3.12626004 2.84463 7.76077986 -3.7262001
		 2.16732001 7.85087013 -4.28831005 1.70237005 7.92692995 -3.56061006 1.94957995 7.69909 -3.34677005
		 2.48723006 7.55601978 -4.011569977;
	setAttr -s 30 ".ed[0:29]"  0 1 0 1 2 0 2 0 1 2 3 0 3 0 0 4 5 0 5 6 0
		 6 4 1 6 7 0 7 4 0 8 9 0 9 10 0 10 8 1 10 11 0 11 8 0 12 13 0 13 14 0 14 12 1 14 15 0
		 15 12 0 16 17 0 17 18 0 18 16 1 18 19 0 19 16 0 20 21 0 21 22 0 22 20 1 22 23 0 23 20 0;
	setAttr -s 24 ".n[0:23]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 12 -ch 36 ".fc[0:11]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 -3
		mu 0 3 2 3 0
		f 3 5 6 7
		mu 0 3 4 5 6
		f 3 8 9 -8
		mu 0 3 6 7 4
		f 3 10 11 12
		mu 0 3 8 9 10
		f 3 13 14 -13
		mu 0 3 10 11 8
		f 3 15 16 17
		mu 0 3 12 13 14
		f 3 18 19 -18
		mu 0 3 14 15 12
		f 3 20 21 22
		mu 0 3 16 17 18
		f 3 23 24 -23
		mu 0 3 18 19 16
		f 3 25 26 27
		mu 0 3 20 21 22
		f 3 28 29 -28
		mu 0 3 22 23 20;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_43_SINGLE";
	rename -uid "5450B6E3-4D7E-8876-5DCD-31BC0250FA45";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_43_SINGLEShape" -p "Joint_1_Object_43_SINGLE";
	rename -uid "8081EF1C-4621-7EF7-57F1-23B79754FF04";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".ccls" -type "string" "colorSet0";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_43_SINGLEShapeOrig" -p "Joint_1_Object_43_SINGLE";
	rename -uid "45ADF722-4181-D5F2-F03F-B995672A030E";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 6 ".uvst[0].uvsp[0:5]" -type "float2" 0.25 0 1 0.5 0.75
		 0 0 0.5 0.75 1 0.25 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr -s 12 ".clst[0].clsp[0:11]"  1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
	setAttr -s 6 ".vt[0:5]"  2.1710701 8.32557011 -3.54668999 2.31227994 7.92833996 -3.41263008
		 2.33102012 8.17815018 -3.40831995 1.99237001 8.22319031 -3.68936992 2.13357997 7.82595015 -3.55532002
		 1.97362995 7.97338009 -3.69369006;
	setAttr -s 9 ".ed[0:8]"  0 1 1 1 2 0 2 0 0 3 1 1 0 3 0 3 4 1 4 1 0
		 5 4 0 3 5 0;
	setAttr -s 6 ".n[0:5]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 4 -ch 12 ".fc[0:3]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		mc 0 3 0 2 5
		f 3 3 -1 4
		mu 0 3 3 1 0
		mc 0 3 6 3 1
		f 3 5 6 -4
		mu 0 3 3 4 1
		mc 0 3 7 9 4
		f 3 7 -6 8
		mu 0 3 5 4 3
		mc 0 3 11 10 8;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_44_SINGLE";
	rename -uid "1F78F41F-4F46-17AA-6CB9-2883933B8C15";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_44_SINGLEShape" -p "Joint_1_Object_44_SINGLE";
	rename -uid "91D25A60-4A44-EA12-2D77-2D8D1CFE99FE";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".ccls" -type "string" "colorSet0";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_44_SINGLEShapeOrig" -p "Joint_1_Object_44_SINGLE";
	rename -uid "D364A094-4734-81DD-B365-F68C69001658";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 13 0 11 0.68359399
		 13 0.68359399 11 0 9 0.68359399 9 0 7 0.68359399 7 0 5 0.68359399 5 0 3 0.68359399
		 3 0 1 0.68359399 1 0;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr -s 36 ".clst[0].clsp[0:35]"  1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1;
	setAttr -s 14 ".vt[0:13]"  1.99258995 6.58528996 -4.40123987 1.95638001 6.56051016 -3.66524005
		 1.79641998 6.7079401 -3.80361009 2.31251001 6.29044008 -4.1244998 2.13328004 6.6596899 -3.52389002
		 2.66810989 6.4920001 -3.84046006 2.15201998 6.90950012 -3.51957011 2.70559001 6.99162006 -3.83183002
		 1.99205995 7.056930065 -3.65793991 2.38566995 7.28646994 -4.1085701 1.81335998 6.95453978 -3.80063009
		 2.02828002 7.081709862 -4.39393997 1.79641998 6.7079401 -3.80361009 1.99258995 6.58528996 -4.40123987;
	setAttr -s 25 ".ed[0:24]"  0 1 1 1 2 0 2 0 0 3 1 1 0 3 0 3 4 1 4 1 0
		 5 4 1 3 5 0 5 6 1 6 4 0 7 6 1 5 7 0 7 8 1 8 6 0 9 8 1 7 9 0 9 10 1 10 8 0 11 10 1
		 9 11 0 11 12 1 12 10 0 13 12 0 11 13 0;
	setAttr -s 14 ".n[0:13]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 12 -ch 36 ".fc[0:11]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		mc 0 3 0 2 5
		f 3 3 -1 4
		mu 0 3 3 1 0
		mc 0 3 6 3 1
		f 3 5 6 -4
		mu 0 3 3 4 1
		mc 0 3 7 9 4
		f 3 7 -6 8
		mu 0 3 5 4 3
		mc 0 3 12 10 8
		f 3 9 10 -8
		mu 0 3 5 6 4
		mc 0 3 13 15 11
		f 3 11 -10 12
		mu 0 3 7 6 5
		mc 0 3 18 16 14
		f 3 13 14 -12
		mu 0 3 7 8 6
		mc 0 3 19 21 17
		f 3 15 -14 16
		mu 0 3 9 8 7
		mc 0 3 24 22 20
		f 3 17 18 -16
		mu 0 3 9 10 8
		mc 0 3 25 27 23
		f 3 19 -18 20
		mu 0 3 11 10 9
		mc 0 3 30 28 26
		f 3 21 22 -20
		mu 0 3 11 12 10
		mc 0 3 31 33 29
		f 3 23 -22 24
		mu 0 3 13 12 11
		mc 0 3 35 34 32;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_45_SINGLE";
	rename -uid "FAB5BA6D-43F7-B33D-BBA8-48BEEB7647C6";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_45_SINGLEShape" -p "Joint_1_Object_45_SINGLE";
	rename -uid "8A564EED-47D0-047A-D946-C5829E4D7F7E";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_45_SINGLEShapeOrig" -p "Joint_1_Object_45_SINGLE";
	rename -uid "0B95DCBB-43F8-712B-C761-5CA15F74562A";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 24 ".uvst[0].uvsp[0:23]" -type "float2" 2.33203006 -2 2.33203006
		 1 1.66796994 1 1.66796994 -2 3 -2 3 1 2.33203006 1 2.33203006 -2 1.66796994 -2 1.66796994
		 1 1 1 1 -2 1 -2 1 1 0.33203101 1 0.33203101 -2 3.66796994 -2 3.66796994 1 3 1 3 -2
		 4.33202982 -2 4.33202982 1 3.66796994 1 3.66796994 -2;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 24 ".vt[0:23]"  2.70559001 6.99162006 -3.83183002 2.078190088 6.97459984 -3.23385
		 1.83098996 7.20243979 -3.44770002 2.38566995 7.28646994 -4.1085701 2.66810989 6.4920001 -3.84046006
		 2.049230099 6.58853006 -3.24052 2.078190088 6.97459984 -3.23385 2.70559001 6.99162006 -3.83183002
		 2.38566995 7.28646994 -4.1085701 1.83098996 7.20243979 -3.44770002 1.55481994 7.044219971 -3.66821003
		 2.02828002 7.081709862 -4.39393997 2.02828002 7.081709862 -4.39393997 1.55481994 7.044219971 -3.66821003
		 1.52765 6.66134977 -3.67354012 1.99258995 6.58528996 -4.40123987 2.31251001 6.29044008 -4.1244998
		 1.77486002 6.43350983 -3.45970011 2.049230099 6.58853006 -3.24052 2.66810989 6.4920001 -3.84046006
		 1.99258995 6.58528996 -4.40123987 1.52765 6.66134977 -3.67354012 1.77486002 6.43350983 -3.45970011
		 2.31251001 6.29044008 -4.1244998;
	setAttr -s 30 ".ed[0:29]"  0 1 0 1 2 0 2 0 1 2 3 0 3 0 0 4 5 0 5 6 0
		 6 4 1 6 7 0 7 4 0 8 9 0 9 10 0 10 8 1 10 11 0 11 8 0 12 13 0 13 14 0 14 12 1 14 15 0
		 15 12 0 16 17 0 17 18 0 18 16 1 18 19 0 19 16 0 20 21 0 21 22 0 22 20 1 22 23 0 23 20 0;
	setAttr -s 24 ".n[0:23]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 12 -ch 36 ".fc[0:11]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 -3
		mu 0 3 2 3 0
		f 3 5 6 7
		mu 0 3 4 5 6
		f 3 8 9 -8
		mu 0 3 6 7 4
		f 3 10 11 12
		mu 0 3 8 9 10
		f 3 13 14 -13
		mu 0 3 10 11 8
		f 3 15 16 17
		mu 0 3 12 13 14
		f 3 18 19 -18
		mu 0 3 14 15 12
		f 3 20 21 22
		mu 0 3 16 17 18
		f 3 23 24 -23
		mu 0 3 18 19 16
		f 3 25 26 27
		mu 0 3 20 21 22
		f 3 28 29 -28
		mu 0 3 22 23 20;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_46_SINGLE";
	rename -uid "13BAD7CD-4E3B-74D5-6507-6A929D11FBF5";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_46_SINGLEShape" -p "Joint_1_Object_46_SINGLE";
	rename -uid "037EE91A-4DD9-E6DE-493C-1AA29AA60984";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".ccls" -type "string" "colorSet0";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_46_SINGLEShapeOrig" -p "Joint_1_Object_46_SINGLE";
	rename -uid "6A8D4367-4AEF-3B8E-D236-8996FDE40F3D";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 6 ".uvst[0].uvsp[0:5]" -type "float2" 0.25 0 1 0.5 0.75
		 0 0 0.5 0.75 1 0.25 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr -s 12 ".clst[0].clsp[0:11]"  1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
	setAttr -s 6 ".vt[0:5]"  1.99205995 7.056930065 -3.65793991 2.13328004 6.6596899 -3.52389002
		 2.15201998 6.90950012 -3.51957011 1.81335998 6.95453978 -3.80063009 1.95638001 6.56051016 -3.66524005
		 1.79641998 6.7079401 -3.80361009;
	setAttr -s 9 ".ed[0:8]"  0 1 1 1 2 0 2 0 0 3 1 1 0 3 0 3 4 1 4 1 0
		 5 4 0 3 5 0;
	setAttr -s 6 ".n[0:5]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 4 -ch 12 ".fc[0:3]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		mc 0 3 0 2 5
		f 3 3 -1 4
		mu 0 3 3 1 0
		mc 0 3 6 3 1
		f 3 5 6 -4
		mu 0 3 3 4 1
		mc 0 3 7 9 4
		f 3 7 -6 8
		mu 0 3 5 4 3
		mc 0 3 11 10 8;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_47_SINGLE";
	rename -uid "37403132-4F71-9B9A-AB6B-6D899E6EFD00";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_47_SINGLEShape" -p "Joint_1_Object_47_SINGLE";
	rename -uid "9AB5EB6F-40CE-086E-B29E-0EB3080857E8";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".ccls" -type "string" "colorSet0";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_47_SINGLEShapeOrig" -p "Joint_1_Object_47_SINGLE";
	rename -uid "DFB019E5-45F6-CC60-7488-008DBC67D8B5";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 13 0 11 0.68359399
		 13 0.68359399 11 0 9 0.68359399 9 0 7 0.68359399 7 0 5 0.68359399 5 0 3 0.68359399
		 3 0 1 0.68359399 1 0;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr -s 36 ".clst[0].clsp[0:35]"  1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1;
	setAttr -s 14 ".vt[0:13]"  3.065890074 8.16676998 -3.95700002 3.03215003 8.14185047 -3.22400999
		 2.87220001 8.28927994 -3.36238003 3.38579988 7.8719101 -3.68025994 3.20905995 8.24102974 -3.08265996
		 3.7414 8.073479652 -3.39621997 3.22779989 8.49083996 -3.078340054 3.77888989 8.57310009 -3.38758993
		 3.067840099 8.63827038 -3.21671009 3.45897007 8.86795044 -3.66433001 2.88913989 8.53588009 -3.35940003
		 3.10156989 8.66318035 -3.94970012 2.87220001 8.28927994 -3.36238003 3.065890074 8.16676998 -3.95700002;
	setAttr -s 25 ".ed[0:24]"  0 1 1 1 2 0 2 0 0 3 1 1 0 3 0 3 4 1 4 1 0
		 5 4 1 3 5 0 5 6 1 6 4 0 7 6 1 5 7 0 7 8 1 8 6 0 9 8 1 7 9 0 9 10 1 10 8 0 11 10 1
		 9 11 0 11 12 1 12 10 0 13 12 0 11 13 0;
	setAttr -s 14 ".n[0:13]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 12 -ch 36 ".fc[0:11]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		mc 0 3 0 2 5
		f 3 3 -1 4
		mu 0 3 3 1 0
		mc 0 3 6 3 1
		f 3 5 6 -4
		mu 0 3 3 4 1
		mc 0 3 7 9 4
		f 3 7 -6 8
		mu 0 3 5 4 3
		mc 0 3 12 10 8
		f 3 9 10 -8
		mu 0 3 5 6 4
		mc 0 3 13 15 11
		f 3 11 -10 12
		mu 0 3 7 6 5
		mc 0 3 18 16 14
		f 3 13 14 -12
		mu 0 3 7 8 6
		mc 0 3 19 21 17
		f 3 15 -14 16
		mu 0 3 9 8 7
		mc 0 3 24 22 20
		f 3 17 18 -16
		mu 0 3 9 10 8
		mc 0 3 25 27 23
		f 3 19 -18 20
		mu 0 3 11 10 9
		mc 0 3 30 28 26
		f 3 21 22 -20
		mu 0 3 11 12 10
		mc 0 3 31 33 29
		f 3 23 -22 24
		mu 0 3 13 12 11
		mc 0 3 35 34 32;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_48_SINGLE";
	rename -uid "43915FE4-46CE-7513-7E3A-B39720DB5D31";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_48_SINGLEShape" -p "Joint_1_Object_48_SINGLE";
	rename -uid "C14C0B09-4103-CC14-095A-FC9F81E50936";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_48_SINGLEShapeOrig" -p "Joint_1_Object_48_SINGLE";
	rename -uid "81EFAAEE-4DB8-9975-71C9-6E8A372B7D96";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 24 ".uvst[0].uvsp[0:23]" -type "float2" 2.33203006 -2 2.33203006
		 1 1.66796994 1 1.66796994 -2 3 -2 3 1 2.33203006 1 2.33203006 -2 1.66796994 -2 1.66796994
		 1 1 1 1 -2 1 -2 1 1 0.33203101 1 0.33203101 -2 3.66796994 -2 3.66796994 1 3 1 3 -2
		 4.33202982 -2 4.33202982 1 3.66796994 1 3.66796994 -2;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 24 ".vt[0:23]"  3.77888989 8.57310009 -3.38758993 3.15148997 8.55607986 -2.78960991
		 2.90427995 8.78392029 -3.0034499168 3.45897007 8.86795044 -3.66433001 3.7414 8.073479652 -3.39621997
		 3.12252998 8.17000961 -2.79627991 3.15148997 8.55607986 -2.78960991 3.77888989 8.57310009 -3.38758993
		 3.45897007 8.86795044 -3.66433001 2.90427995 8.78392029 -3.0034499168 2.62810993 8.62569046 -3.22396994
		 3.10156989 8.66318035 -3.94970012 3.10156989 8.66318035 -3.94970012 2.62810993 8.62569046 -3.22396994
		 2.60093999 8.24281979 -3.22930002 3.065890074 8.16676998 -3.95700002 3.38579988 7.8719101 -3.68025994
		 2.84815001 8.014980316 -3.015460014 3.12252998 8.17000961 -2.79627991 3.7414 8.073479652 -3.39621997
		 3.065890074 8.16676998 -3.95700002 2.60093999 8.24281979 -3.22930002 2.84815001 8.014980316 -3.015460014
		 3.38579988 7.8719101 -3.68025994;
	setAttr -s 30 ".ed[0:29]"  0 1 0 1 2 0 2 0 1 2 3 0 3 0 0 4 5 0 5 6 0
		 6 4 1 6 7 0 7 4 0 8 9 0 9 10 0 10 8 1 10 11 0 11 8 0 12 13 0 13 14 0 14 12 1 14 15 0
		 15 12 0 16 17 0 17 18 0 18 16 1 18 19 0 19 16 0 20 21 0 21 22 0 22 20 1 22 23 0 23 20 0;
	setAttr -s 24 ".n[0:23]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 12 -ch 36 ".fc[0:11]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 4 -3
		mu 0 3 2 3 0
		f 3 5 6 7
		mu 0 3 4 5 6
		f 3 8 9 -8
		mu 0 3 6 7 4
		f 3 10 11 12
		mu 0 3 8 9 10
		f 3 13 14 -13
		mu 0 3 10 11 8
		f 3 15 16 17
		mu 0 3 12 13 14
		f 3 18 19 -18
		mu 0 3 14 15 12
		f 3 20 21 22
		mu 0 3 16 17 18
		f 3 23 24 -23
		mu 0 3 18 19 16
		f 3 25 26 27
		mu 0 3 20 21 22
		f 3 28 29 -28
		mu 0 3 22 23 20;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_49_SINGLE";
	rename -uid "1E3780FB-4215-5A3D-A9F4-07B0A42A2B93";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_49_SINGLEShape" -p "Joint_1_Object_49_SINGLE";
	rename -uid "20AFAA09-4B99-D23E-C693-73A9FF17C2F1";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".ccls" -type "string" "colorSet0";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_49_SINGLEShapeOrig" -p "Joint_1_Object_49_SINGLE";
	rename -uid "8E61B90D-4BE1-E60F-1403-7A87E77FAD6B";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 6 ".uvst[0].uvsp[0:5]" -type "float2" 0.25 0 1 0.5 0.75
		 0 0 0.5 0.75 1 0.25 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".clst[0].clsn" -type "string" "colorSet0";
	setAttr -s 12 ".clst[0].clsp[0:11]"  1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
		 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
	setAttr -s 6 ".vt[0:5]"  3.067840099 8.63827038 -3.21671009 3.20905995 8.24102974 -3.08265996
		 3.22779989 8.49083996 -3.078340054 2.88913989 8.53588009 -3.35940003 3.03215003 8.14185047 -3.22400999
		 2.87220001 8.28927994 -3.36238003;
	setAttr -s 9 ".ed[0:8]"  0 1 1 1 2 0 2 0 0 3 1 1 0 3 0 3 4 1 4 1 0
		 5 4 0 3 5 0;
	setAttr -s 6 ".n[0:5]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 4 -ch 12 ".fc[0:3]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		mc 0 3 0 2 5
		f 3 3 -1 4
		mu 0 3 3 1 0
		mc 0 3 6 3 1
		f 3 5 6 -4
		mu 0 3 3 4 1
		mc 0 3 7 9 4
		f 3 7 -6 8
		mu 0 3 5 4 3
		mc 0 3 11 10 8;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_50_SINGLE";
	rename -uid "DF042A38-4190-AD53-BAF8-88A834645362";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_50_SINGLEShape" -p "Joint_1_Object_50_SINGLE";
	rename -uid "657AAA5A-4A88-5E1C-8D88-2BB7E8E3CA3E";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_50_SINGLEShapeOrig" -p "Joint_1_Object_50_SINGLE";
	rename -uid "ACB976CE-44F9-4A9F-46C1-4398E02F71DD";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 81 ".uvst[0].uvsp[0:80]" -type "float2" 0.57421899 0.109375
		 0.59765601 0.0078119999 0.40234399 0.0078119999 0.71484399 0.167969 0.77734399 0.085937001
		 0.82031298 0.27734399 0.91406298 0.222656 0.87890601 0.421875 0.99218798 0.40234399
		 0.87890601 0.578125 0.99218798 0.59765601 0.82031298 0.72265601 0.91406298 0.77734399
		 0.71484399 0.83203101 0.77734399 0.91406298 0.57421899 0.890625 0.59765601 0.99218798
		 0.42578101 0.890625 0.40234399 0.99218798 0.28515601 0.83203101 0.222656 0.91406298
		 0.17968801 0.72265601 0.085937001 0.77734399 0.121094 0.578125 0.0078119999 0.59765601
		 0.121094 0.421875 0.0078119999 0.40234399 0.17968801 0.27734399 0.085937001 0.222656
		 0.28515601 0.167969 0.222656 0.085937001 0.42578101 0.109375 0.44140601 0.183594
		 0.328125 0.234375 0.246094 0.32031301 0.199219 0.4375 0.199219 0.5625 0.246094 0.67968798
		 0.328125 0.765625 0.44140601 0.81640601 0.55859399 0.81640601 0.671875 0.765625 0.75390601
		 0.67968798 0.80078101 0.5625 0.80078101 0.4375 0.75390601 0.32031301 0.671875 0.234375
		 0.55859399 0.183594 0.46093801 0.28906301 0.38281301 0.32031301 0.32421899 0.37890601
		 0.29296899 0.45703101 0.29296899 0.54296899 0.32421899 0.62109399 0.38281301 0.67968798
		 0.46093801 0.71093798 0.53906298 0.71093798 0.61718798 0.67968798 0.67578101 0.62109399
		 0.70703101 0.54296899 0.70703101 0.45703101 0.67578101 0.37890601 0.61718798 0.32031301
		 0.53906298 0.28906301 0.48046899 0.390625 0.44140601 0.40625 0.41015601 0.4375 0.39453101
		 0.47656301 0.39453101 0.52343798 0.41015601 0.5625 0.44140601 0.59375 0.48046899
		 0.609375 0.51953101 0.609375 0.55859399 0.59375 0.58984399 0.5625 0.60546899 0.52343798
		 0.60546899 0.47656301 0.58984399 0.4375 0.55859399 0.40625 0.51953101 0.390625 0.5
		 0.5;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 81 ".vt[0:80]"  4.48001003 8.7971096 -4.19232988 5.073530197 8.8070097 -4.85335016
		 4.89903021 8.96784019 -5.0043001175 4.58361006 8.57538033 -4.097089767 5.18565989 8.56770039 -4.75029993
		 4.61379004 8.31447029 -4.060599804 5.21592999 8.28728962 -4.71287012 4.56308985 8.060119629 -4.091050148
		 5.16352987 8.010230064 -4.74371004 4.44283009 7.84560013 -4.18058014 5.03249979 7.77650023 -4.84126997
		 4.27095985 7.70293999 -4.31584978 4.8443799 7.62452984 -4.98951006 4.068470001 7.65646982 -4.48062992
		 4.62744999 7.57195997 -5.16591978 3.87333012 7.71492004 -4.64402008 4.41481018 7.63196993 -5.34380007
		 3.70852995 7.86681986 -4.7865901 4.24031019 7.79279995 -5.49475002 3.60314012 8.085350037 -4.88316011
		 4.12818003 8.032110214 -5.59779978 3.5729599 8.34626007 -4.91965008 4.097909927 8.31252003 -5.63523006
		 3.62365007 8.60060978 -4.88920021 4.15031004 8.58957958 -5.60439014 3.74391007 8.81513023 -4.79967022
		 4.28134012 8.8233099 -5.50684023 3.91579008 8.95779037 -4.6644001 4.46946001 8.97527981 -5.35860014
		 4.11827993 9.0042600632 -4.49961996 4.68639994 9.027850151 -5.18218994 4.31520987 8.9490099 -4.33488989
		 3.95627999 8.89192009 -3.94439006 3.78590989 8.94209957 -4.087009907 3.60694003 8.89824009 -4.2325201
		 3.45490003 8.77128983 -4.35214996 3.34899998 8.58238983 -4.43099022 3.30360007 8.35715008 -4.45837021
		 3.33000994 8.12886047 -4.42644978 3.41960001 7.93459988 -4.34396982 3.56016994 7.80503988 -4.22237015
		 3.73233008 7.75805998 -4.078430176 3.90949988 7.79870987 -3.9342401 4.061540127 7.92567015 -3.81462002
		 4.16743994 8.11456966 -3.73576999 4.21284008 8.33981037 -3.70840001 4.18823004 8.57129955 -3.73899007
		 4.096849918 8.76235962 -3.82279992 3.65471005 8.77803993 -3.66616011 3.52304006 8.81200027 -3.77617002
		 3.38804007 8.78102016 -3.88602996 3.27146006 8.68451977 -3.97779989 3.19069004 8.54043961 -4.037930012
		 3.1565001 8.36798954 -4.058420181 3.17662001 8.19406033 -4.034100056 3.24368 8.044839859 -3.9721899
		 3.3503201 7.94655991 -3.87995005 3.48200011 7.91261005 -3.7699399 3.61699009 7.94358015 -3.66007996
		 3.7335701 8.04008007 -3.56832004 3.81434989 8.18416023 -3.5081799 3.84853005 8.3566103 -3.48768997
		 3.82840991 8.53054047 -3.51202011 3.76134992 8.67975998 -3.57392001 3.41410995 8.57328987 -3.52610993
		 3.34705997 8.59138012 -3.58216 3.2813499 8.57909966 -3.63575006 3.22363997 8.5351696 -3.68134999
		 3.18415999 8.46473026 -3.7107501 3.16827989 8.37738991 -3.71994996 3.18013 8.29362011 -3.70644999
		 3.21667004 8.22109985 -3.67311001 3.26998997 8.17195988 -3.62699008 3.33523989 8.15065956 -3.57226992
		 3.40093994 8.16294956 -3.5186801 3.46044993 8.21008015 -3.47175002 3.4999299 8.28052044 -3.44234991
		 3.51401997 8.36466026 -3.43448997 3.50217009 8.44841957 -3.44798994 3.4674201 8.52414989 -3.47999001
		 3.28495002 8.37570953 -3.50725007;
	setAttr -s 224 ".ed";
	setAttr ".ed[0:165]"  0 1 1 1 2 0 2 0 1 3 1 1 0 3 1 3 4 1 4 1 0 5 4 1 3 5 1
		 5 6 1 6 4 0 7 6 1 5 7 1 7 8 1 8 6 0 9 8 1 7 9 1 9 10 1 10 8 0 11 10 1 9 11 1 11 12 1
		 12 10 0 13 12 1 11 13 1 13 14 1 14 12 0 15 14 1 13 15 1 15 16 1 16 14 0 17 16 1 15 17 1
		 17 18 1 18 16 0 19 18 1 17 19 1 19 20 1 20 18 0 21 20 1 19 21 1 21 22 1 22 20 0 23 22 1
		 21 23 1 23 24 1 24 22 0 25 24 1 23 25 1 25 26 1 26 24 0 27 26 1 25 27 1 27 28 1 28 26 0
		 29 28 1 27 29 1 29 30 1 30 28 0 31 30 1 29 31 1 31 2 1 2 30 0 31 0 1 31 32 1 32 0 1
		 29 33 1 33 31 1 33 32 1 27 34 1 34 29 1 34 33 1 27 35 1 35 34 1 25 35 1 23 36 1 36 25 1
		 36 35 1 21 37 1 37 23 1 37 36 1 19 38 1 38 21 1 38 37 1 19 39 1 39 38 1 17 39 1 15 39 1
		 13 40 1 40 15 1 40 39 1 11 41 1 41 13 1 41 40 1 9 42 1 42 11 1 42 41 1 9 43 1 43 42 1
		 7 43 1 5 44 1 44 7 1 44 43 1 3 45 1 45 5 1 45 44 1 0 46 1 46 3 1 46 45 1 0 47 1 47 46 1
		 32 47 1 32 48 1 48 47 1 33 49 1 49 32 1 49 48 1 34 50 1 50 33 1 50 49 1 34 51 1 51 50 1
		 35 51 1 36 52 1 52 35 1 52 51 1 37 53 1 53 36 1 53 52 1 38 54 1 54 37 1 54 53 1 38 55 1
		 55 54 1 39 55 1 40 55 1 41 56 1 56 40 1 56 55 1 42 57 1 57 41 1 57 56 1 42 58 1 58 57 1
		 43 58 1 44 59 1 59 43 1 59 58 1 45 60 1 60 44 1 60 59 1 46 61 1 61 45 1 61 60 1 46 62 1
		 62 61 1 47 62 1 48 63 1 63 47 1 63 62 1 48 64 1 64 63 1 49 65 1 65 48 1 65 64 1 49 66 1;
	setAttr ".ed[166:223]" 66 65 1 50 66 1 51 67 1 67 50 1 67 66 1 52 68 1 68 51 1
		 68 67 1 53 69 1 69 52 1 69 68 1 53 70 1 70 69 1 54 70 1 55 71 1 71 54 1 56 71 1 71 70 1
		 57 72 1 72 56 1 72 71 1 57 73 1 73 72 1 58 73 1 59 74 1 74 58 1 74 73 1 60 75 1 75 59 1
		 75 74 1 61 76 1 76 60 1 76 75 1 61 77 1 77 76 1 62 77 1 63 78 1 78 62 1 78 77 1 64 79 1
		 79 63 1 79 78 1 64 80 1 80 79 1 65 80 1 66 80 1 67 80 1 68 80 1 69 80 1 70 80 1 71 80 1
		 72 80 1 73 80 1 74 80 1 75 80 1 76 80 1 77 80 1 78 80 1;
	setAttr -s 81 ".n[0:80]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 144 -ch 432 ".fc[0:143]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 -1 4
		mu 0 3 3 1 0
		f 3 5 6 -4
		mu 0 3 3 4 1
		f 3 7 -6 8
		mu 0 3 5 4 3
		f 3 9 10 -8
		mu 0 3 5 6 4
		f 3 11 -10 12
		mu 0 3 7 6 5
		f 3 13 14 -12
		mu 0 3 7 8 6
		f 3 15 -14 16
		mu 0 3 9 8 7
		f 3 17 18 -16
		mu 0 3 9 10 8
		f 3 19 -18 20
		mu 0 3 11 10 9
		f 3 21 22 -20
		mu 0 3 11 12 10
		f 3 23 -22 24
		mu 0 3 13 12 11
		f 3 25 26 -24
		mu 0 3 13 14 12
		f 3 27 -26 28
		mu 0 3 15 14 13
		f 3 29 30 -28
		mu 0 3 15 16 14
		f 3 31 -30 32
		mu 0 3 17 16 15
		f 3 33 34 -32
		mu 0 3 17 18 16
		f 3 35 -34 36
		mu 0 3 19 18 17
		f 3 37 38 -36
		mu 0 3 19 20 18
		f 3 39 -38 40
		mu 0 3 21 20 19
		f 3 41 42 -40
		mu 0 3 21 22 20
		f 3 43 -42 44
		mu 0 3 23 22 21
		f 3 45 46 -44
		mu 0 3 23 24 22
		f 3 47 -46 48
		mu 0 3 25 24 23
		f 3 49 50 -48
		mu 0 3 25 26 24
		f 3 51 -50 52
		mu 0 3 27 26 25
		f 3 53 54 -52
		mu 0 3 27 28 26
		f 3 55 -54 56
		mu 0 3 29 28 27
		f 3 57 58 -56
		mu 0 3 29 30 28
		f 3 59 -58 60
		mu 0 3 31 30 29
		f 3 61 62 -60
		mu 0 3 31 2 30
		f 3 63 -3 -62
		mu 0 3 31 0 2
		f 3 64 65 -64
		mu 0 3 31 32 0
		f 3 66 67 -61
		mu 0 3 29 33 31
		f 3 -68 68 -65
		mu 0 3 31 33 32
		f 3 69 70 -57
		mu 0 3 27 34 29
		f 3 -71 71 -67
		mu 0 3 29 34 33
		f 3 72 73 -70
		mu 0 3 27 35 34
		f 3 74 -73 -53
		mu 0 3 25 35 27
		f 3 75 76 -49
		mu 0 3 23 36 25
		f 3 -77 77 -75
		mu 0 3 25 36 35
		f 3 78 79 -45
		mu 0 3 21 37 23
		f 3 -80 80 -76
		mu 0 3 23 37 36
		f 3 81 82 -41
		mu 0 3 19 38 21
		f 3 -83 83 -79
		mu 0 3 21 38 37
		f 3 84 85 -82
		mu 0 3 19 39 38
		f 3 86 -85 -37
		mu 0 3 17 39 19
		f 3 87 -87 -33
		mu 0 3 15 39 17
		f 3 88 89 -29
		mu 0 3 13 40 15
		f 3 -90 90 -88
		mu 0 3 15 40 39
		f 3 91 92 -25
		mu 0 3 11 41 13
		f 3 -93 93 -89
		mu 0 3 13 41 40
		f 3 94 95 -21
		mu 0 3 9 42 11
		f 3 -96 96 -92
		mu 0 3 11 42 41
		f 3 97 98 -95
		mu 0 3 9 43 42
		f 3 99 -98 -17
		mu 0 3 7 43 9
		f 3 100 101 -13
		mu 0 3 5 44 7
		f 3 -102 102 -100
		mu 0 3 7 44 43
		f 3 103 104 -9
		mu 0 3 3 45 5
		f 3 -105 105 -101
		mu 0 3 5 45 44
		f 3 106 107 -5
		mu 0 3 0 46 3
		f 3 -108 108 -104
		mu 0 3 3 46 45
		f 3 109 110 -107
		mu 0 3 0 47 46
		f 3 111 -110 -66
		mu 0 3 32 47 0
		f 3 112 113 -112
		mu 0 3 32 48 47
		f 3 114 115 -69
		mu 0 3 33 49 32
		f 3 -116 116 -113
		mu 0 3 32 49 48
		f 3 117 118 -72
		mu 0 3 34 50 33
		f 3 -119 119 -115
		mu 0 3 33 50 49
		f 3 120 121 -118
		mu 0 3 34 51 50
		f 3 122 -121 -74
		mu 0 3 35 51 34
		f 3 123 124 -78
		mu 0 3 36 52 35
		f 3 -125 125 -123
		mu 0 3 35 52 51
		f 3 126 127 -81
		mu 0 3 37 53 36
		f 3 -128 128 -124
		mu 0 3 36 53 52
		f 3 129 130 -84
		mu 0 3 38 54 37
		f 3 -131 131 -127
		mu 0 3 37 54 53
		f 3 132 133 -130
		mu 0 3 38 55 54
		f 3 134 -133 -86
		mu 0 3 39 55 38
		f 3 135 -135 -91
		mu 0 3 40 55 39
		f 3 136 137 -94
		mu 0 3 41 56 40
		f 3 -138 138 -136
		mu 0 3 40 56 55
		f 3 139 140 -97
		mu 0 3 42 57 41
		f 3 -141 141 -137
		mu 0 3 41 57 56
		f 3 142 143 -140
		mu 0 3 42 58 57
		f 3 144 -143 -99
		mu 0 3 43 58 42
		f 3 145 146 -103
		mu 0 3 44 59 43
		f 3 -147 147 -145
		mu 0 3 43 59 58
		f 3 148 149 -106
		mu 0 3 45 60 44
		f 3 -150 150 -146
		mu 0 3 44 60 59
		f 3 151 152 -109
		mu 0 3 46 61 45
		f 3 -153 153 -149
		mu 0 3 45 61 60
		f 3 154 155 -152
		mu 0 3 46 62 61
		f 3 156 -155 -111
		mu 0 3 47 62 46
		f 3 157 158 -114
		mu 0 3 48 63 47
		f 3 -159 159 -157
		mu 0 3 47 63 62
		f 3 160 161 -158
		mu 0 3 48 64 63
		f 3 162 163 -117
		mu 0 3 49 65 48
		f 3 -164 164 -161
		mu 0 3 48 65 64
		f 3 165 166 -163
		mu 0 3 49 66 65
		f 3 167 -166 -120
		mu 0 3 50 66 49
		f 3 168 169 -122
		mu 0 3 51 67 50
		f 3 -170 170 -168
		mu 0 3 50 67 66
		f 3 171 172 -126
		mu 0 3 52 68 51
		f 3 -173 173 -169
		mu 0 3 51 68 67
		f 3 174 175 -129
		mu 0 3 53 69 52
		f 3 -176 176 -172
		mu 0 3 52 69 68
		f 3 177 178 -175
		mu 0 3 53 70 69
		f 3 179 -178 -132
		mu 0 3 54 70 53
		f 3 180 181 -134
		mu 0 3 55 71 54
		f 3 182 -181 -139
		mu 0 3 56 71 55
		f 3 -182 183 -180
		mu 0 3 54 71 70
		f 3 184 185 -142
		mu 0 3 57 72 56
		f 3 -186 186 -183
		mu 0 3 56 72 71
		f 3 187 188 -185
		mu 0 3 57 73 72
		f 3 189 -188 -144
		mu 0 3 58 73 57
		f 3 190 191 -148
		mu 0 3 59 74 58
		f 3 -192 192 -190
		mu 0 3 58 74 73
		f 3 193 194 -151
		mu 0 3 60 75 59
		f 3 -195 195 -191
		mu 0 3 59 75 74
		f 3 196 197 -154
		mu 0 3 61 76 60
		f 3 -198 198 -194
		mu 0 3 60 76 75
		f 3 199 200 -197
		mu 0 3 61 77 76
		f 3 201 -200 -156
		mu 0 3 62 77 61
		f 3 202 203 -160
		mu 0 3 63 78 62
		f 3 -204 204 -202
		mu 0 3 62 78 77
		f 3 205 206 -162
		mu 0 3 64 79 63
		f 3 -207 207 -203
		mu 0 3 63 79 78
		f 3 208 209 -206
		mu 0 3 64 80 79
		f 3 210 -209 -165
		mu 0 3 65 80 64
		f 3 211 -211 -167
		mu 0 3 66 80 65
		f 3 212 -212 -171
		mu 0 3 67 80 66
		f 3 213 -213 -174
		mu 0 3 68 80 67
		f 3 214 -214 -177
		mu 0 3 69 80 68
		f 3 215 -215 -179
		mu 0 3 70 80 69
		f 3 216 -216 -184
		mu 0 3 71 80 70
		f 3 217 -217 -187
		mu 0 3 72 80 71
		f 3 218 -218 -189
		mu 0 3 73 80 72
		f 3 219 -219 -193
		mu 0 3 74 80 73
		f 3 220 -220 -196
		mu 0 3 75 80 74
		f 3 221 -221 -199
		mu 0 3 76 80 75
		f 3 222 -222 -201
		mu 0 3 77 80 76
		f 3 223 -223 -205
		mu 0 3 78 80 77
		f 3 -208 -210 -224
		mu 0 3 78 79 80;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_51_SINGLE";
	rename -uid "235B6A60-47E3-C7B3-86F0-D189B2A9CE7A";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_51_SINGLEShape" -p "Joint_1_Object_51_SINGLE";
	rename -uid "0859620E-47C3-0C0C-7262-298C990C4990";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_51_SINGLEShapeOrig" -p "Joint_1_Object_51_SINGLE";
	rename -uid "388F1D4A-4323-8072-3691-4697D7F660EA";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 81 ".uvst[0].uvsp[0:80]" -type "float2" 0.57421899 0.109375
		 0.59765601 0.0078119999 0.40234399 0.0078119999 0.71484399 0.167969 0.77734399 0.085937001
		 0.82031298 0.27734399 0.91406298 0.222656 0.87890601 0.421875 0.99218798 0.40234399
		 0.87890601 0.578125 0.99218798 0.59765601 0.82031298 0.72265601 0.91406298 0.77734399
		 0.71484399 0.83203101 0.77734399 0.91406298 0.57421899 0.890625 0.59765601 0.99218798
		 0.42578101 0.890625 0.40234399 0.99218798 0.28515601 0.83203101 0.222656 0.91406298
		 0.17968801 0.72265601 0.085937001 0.77734399 0.121094 0.578125 0.0078119999 0.59765601
		 0.121094 0.421875 0.0078119999 0.40234399 0.17968801 0.27734399 0.085937001 0.222656
		 0.28515601 0.167969 0.222656 0.085937001 0.42578101 0.109375 0.44140601 0.183594
		 0.328125 0.234375 0.246094 0.32031301 0.199219 0.4375 0.199219 0.5625 0.246094 0.67968798
		 0.328125 0.765625 0.44140601 0.81640601 0.55859399 0.81640601 0.671875 0.765625 0.75390601
		 0.67968798 0.80078101 0.5625 0.80078101 0.4375 0.75390601 0.32031301 0.671875 0.234375
		 0.55859399 0.183594 0.46093801 0.28906301 0.38281301 0.32031301 0.32421899 0.37890601
		 0.29296899 0.45703101 0.29296899 0.54296899 0.32421899 0.62109399 0.38281301 0.67968798
		 0.46093801 0.71093798 0.53906298 0.71093798 0.61718798 0.67968798 0.67578101 0.62109399
		 0.70703101 0.54296899 0.70703101 0.45703101 0.67578101 0.37890601 0.61718798 0.32031301
		 0.53906298 0.28906301 0.48046899 0.390625 0.44140601 0.40625 0.41015601 0.4375 0.39453101
		 0.47656301 0.39453101 0.52343798 0.41015601 0.5625 0.44140601 0.59375 0.48046899
		 0.609375 0.51953101 0.609375 0.55859399 0.59375 0.58984399 0.5625 0.60546899 0.52343798
		 0.60546899 0.47656301 0.58984399 0.4375 0.55859399 0.40625 0.51953101 0.390625 0.5
		 0.5;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 81 ".vt[0:80]"  3.58143997 8.48122025 -4.52364016 4.17497015 8.49112034 -5.18465996
		 4.00047016144 8.65194988 -5.33560991 3.68504 8.25948048 -4.42840004 4.28708982 8.25181007 -5.081610203
		 3.71701002 8.0017795563 -4.39058018 4.31915998 7.97459984 -5.042850018 3.66874003 7.74519014 -4.41892004
		 4.26495981 7.69433022 -5.075019836 3.54668999 7.52748013 -4.50979996 4.13572979 7.46380997 -5.17123985
		 3.37239003 7.38704014 -4.64716005 3.94581008 7.30862999 -5.32081985 3.1717 7.34378004 -4.81060982
		 3.73066998 7.25926018 -5.49589014 2.97477007 7.39903021 -4.97533989 3.51802993 7.31928015 -5.67377996
		 2.81238008 7.54868984 -5.1157999 3.34352994 7.48011017 -5.82472992 2.7063601 7.77265978 -5.21314001
		 3.23141003 7.71940994 -5.92777014 2.67682004 8.028129578 -5.24885988 3.19934011 7.99662018 -5.96653986
		 2.72508001 8.28470993 -5.22051001 3.25354004 8.2768898 -5.93437004 2.84714007 8.50242996 -5.1296401
		 3.38277006 8.50741005 -5.83815002 3.021440029 8.64286041 -4.99228001 3.57268 8.66259003 -5.68857002
		 3.21971011 8.68836021 -4.83093023 3.78783011 8.71195984 -5.51350021 3.41905999 8.63088036 -4.66410017
		 3.059499979 8.57923031 -4.27437019 2.88734007 8.62621021 -4.41832018 2.71258998 8.58331966 -4.56040001
		 2.55813003 8.45860004 -4.68211985 2.45042992 8.26648998 -4.76230001 2.40745997 8.039019585 -4.78759003
		 2.43144011 7.81296015 -4.75776005 2.52102995 7.61870003 -4.67528009 2.66402006 7.48690987 -4.55158997
		 2.83617997 7.43992996 -4.40763998 3.010940075 7.48282003 -4.26556015 3.16297007 7.60976982 -4.14592981
		 3.27066994 7.80187988 -4.065750122 3.31607008 8.027119637 -4.038370132 3.29208994 8.25317001 -4.068200111
		 3.20249009 8.44744015 -4.15067005 2.75613999 8.46214962 -3.9974699 2.62626004 8.4993 -4.10615015
		 2.49369001 8.4660902 -4.2139101 2.37711 8.36958981 -4.30566978 2.29453993 8.22231007 -4.36714983
		 2.26036 8.049860001 -4.38764 2.27804995 7.87816 -4.36540985 2.34691 7.73215008 -4.3021698
		 2.4535501 7.63386011 -4.20991993 2.58343005 7.59671021 -4.10125017 2.71842003 7.62768984 -3.9914
		 2.83501005 7.72419024 -3.89963007 2.91757011 7.87146997 -3.83815002 2.95176005 8.043919563 -3.81767011
		 2.93163991 8.21784973 -3.84198999 2.86278009 8.36386013 -3.90523005 2.51553988 8.25739956 -3.85741997
		 2.45027995 8.27869034 -3.91213989 2.38279009 8.26319981 -3.9670701 2.3250699 8.21926975 -4.012660027
		 2.28558993 8.14883041 -4.042059898 2.27150011 8.064689636 -4.049920082 2.28155994 7.9777298 -4.037759781
		 2.31809998 7.9052 -4.0044198036 2.37384009 7.85382986 -3.95619988 2.43909001 7.83253002 -3.90148997
		 2.50658989 7.84802008 -3.84656 2.56188011 7.89418983 -3.80306005 2.6013701 7.96462011 -3.77365994
		 2.61787009 8.04652977 -3.76370001 2.60782003 8.1335001 -3.77587008 2.57128 8.20602036 -3.80920005
		 2.38637996 8.059820175 -3.8385601;
	setAttr -s 224 ".ed";
	setAttr ".ed[0:165]"  0 1 1 1 2 0 2 0 1 3 1 1 0 3 1 3 4 1 4 1 0 5 4 1 3 5 1
		 5 6 1 6 4 0 7 6 1 5 7 1 7 8 1 8 6 0 9 8 1 7 9 1 9 10 1 10 8 0 11 10 1 9 11 1 11 12 1
		 12 10 0 13 12 1 11 13 1 13 14 1 14 12 0 15 14 1 13 15 1 15 16 1 16 14 0 17 16 1 15 17 1
		 17 18 1 18 16 0 19 18 1 17 19 1 19 20 1 20 18 0 21 20 1 19 21 1 21 22 1 22 20 0 23 22 1
		 21 23 1 23 24 1 24 22 0 25 24 1 23 25 1 25 26 1 26 24 0 27 26 1 25 27 1 27 28 1 28 26 0
		 29 28 1 27 29 1 29 30 1 30 28 0 31 2 1 2 30 0 30 31 1 31 0 1 29 31 1 31 32 1 32 0 1
		 31 33 1 33 32 1 29 33 1 27 34 1 34 29 1 34 33 1 25 35 1 35 27 1 35 34 1 25 36 1 36 35 1
		 23 36 1 21 37 1 37 23 1 37 36 1 19 38 1 38 21 1 38 37 1 19 39 1 39 38 1 17 39 1 15 39 1
		 13 40 1 40 15 1 40 39 1 11 41 1 41 13 1 41 40 1 11 42 1 42 41 1 9 42 1 7 43 1 43 9 1
		 43 42 1 5 44 1 44 7 1 44 43 1 3 45 1 45 5 1 45 44 1 3 46 1 46 45 1 0 46 1 32 47 1
		 47 0 1 47 46 1 32 48 1 48 47 1 33 49 1 49 32 1 49 48 1 34 50 1 50 33 1 50 49 1 34 51 1
		 51 50 1 35 51 1 36 52 1 52 35 1 52 51 1 37 53 1 53 36 1 53 52 1 38 54 1 54 37 1 54 53 1
		 38 55 1 55 54 1 39 55 1 40 55 1 41 56 1 56 40 1 56 55 1 42 57 1 57 41 1 57 56 1 42 58 1
		 58 57 1 43 58 1 44 59 1 59 43 1 59 58 1 45 60 1 60 44 1 60 59 1 46 61 1 61 45 1 61 60 1
		 46 62 1 62 61 1 47 62 1 48 63 1 63 47 1 63 62 1 48 64 1 64 63 1 49 65 1 65 48 1 65 64 1
		 50 66 1;
	setAttr ".ed[166:223]" 66 49 1 66 65 1 50 67 1 67 66 1 51 67 1 52 68 1 68 51 1
		 68 67 1 53 69 1 69 52 1 69 68 1 54 70 1 70 53 1 70 69 1 54 71 1 71 70 1 55 71 1 56 71 1
		 57 72 1 72 56 1 72 71 1 58 73 1 73 57 1 73 72 1 58 74 1 74 73 1 59 74 1 60 75 1 75 59 1
		 75 74 1 61 76 1 76 60 1 76 75 1 61 77 1 77 76 1 62 77 1 63 78 1 78 62 1 78 77 1 64 79 1
		 79 63 1 79 78 1 64 80 1 80 79 1 65 80 1 66 80 1 67 80 1 68 80 1 69 80 1 70 80 1 71 80 1
		 72 80 1 73 80 1 74 80 1 75 80 1 76 80 1 77 80 1 78 80 1;
	setAttr -s 81 ".n[0:80]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 144 -ch 432 ".fc[0:143]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 -1 4
		mu 0 3 3 1 0
		f 3 5 6 -4
		mu 0 3 3 4 1
		f 3 7 -6 8
		mu 0 3 5 4 3
		f 3 9 10 -8
		mu 0 3 5 6 4
		f 3 11 -10 12
		mu 0 3 7 6 5
		f 3 13 14 -12
		mu 0 3 7 8 6
		f 3 15 -14 16
		mu 0 3 9 8 7
		f 3 17 18 -16
		mu 0 3 9 10 8
		f 3 19 -18 20
		mu 0 3 11 10 9
		f 3 21 22 -20
		mu 0 3 11 12 10
		f 3 23 -22 24
		mu 0 3 13 12 11
		f 3 25 26 -24
		mu 0 3 13 14 12
		f 3 27 -26 28
		mu 0 3 15 14 13
		f 3 29 30 -28
		mu 0 3 15 16 14
		f 3 31 -30 32
		mu 0 3 17 16 15
		f 3 33 34 -32
		mu 0 3 17 18 16
		f 3 35 -34 36
		mu 0 3 19 18 17
		f 3 37 38 -36
		mu 0 3 19 20 18
		f 3 39 -38 40
		mu 0 3 21 20 19
		f 3 41 42 -40
		mu 0 3 21 22 20
		f 3 43 -42 44
		mu 0 3 23 22 21
		f 3 45 46 -44
		mu 0 3 23 24 22
		f 3 47 -46 48
		mu 0 3 25 24 23
		f 3 49 50 -48
		mu 0 3 25 26 24
		f 3 51 -50 52
		mu 0 3 27 26 25
		f 3 53 54 -52
		mu 0 3 27 28 26
		f 3 55 -54 56
		mu 0 3 29 28 27
		f 3 57 58 -56
		mu 0 3 29 30 28
		f 3 59 60 61
		mu 0 3 31 2 30
		f 3 62 -3 -60
		mu 0 3 31 0 2
		f 3 -62 -58 63
		mu 0 3 31 30 29
		f 3 64 65 -63
		mu 0 3 31 32 0
		f 3 66 67 -65
		mu 0 3 31 33 32
		f 3 68 -67 -64
		mu 0 3 29 33 31
		f 3 69 70 -57
		mu 0 3 27 34 29
		f 3 -71 71 -69
		mu 0 3 29 34 33
		f 3 72 73 -53
		mu 0 3 25 35 27
		f 3 -74 74 -70
		mu 0 3 27 35 34
		f 3 75 76 -73
		mu 0 3 25 36 35
		f 3 77 -76 -49
		mu 0 3 23 36 25
		f 3 78 79 -45
		mu 0 3 21 37 23
		f 3 -80 80 -78
		mu 0 3 23 37 36
		f 3 81 82 -41
		mu 0 3 19 38 21
		f 3 -83 83 -79
		mu 0 3 21 38 37
		f 3 84 85 -82
		mu 0 3 19 39 38
		f 3 86 -85 -37
		mu 0 3 17 39 19
		f 3 87 -87 -33
		mu 0 3 15 39 17
		f 3 88 89 -29
		mu 0 3 13 40 15
		f 3 -90 90 -88
		mu 0 3 15 40 39
		f 3 91 92 -25
		mu 0 3 11 41 13
		f 3 -93 93 -89
		mu 0 3 13 41 40
		f 3 94 95 -92
		mu 0 3 11 42 41
		f 3 96 -95 -21
		mu 0 3 9 42 11
		f 3 97 98 -17
		mu 0 3 7 43 9
		f 3 -99 99 -97
		mu 0 3 9 43 42
		f 3 100 101 -13
		mu 0 3 5 44 7
		f 3 -102 102 -98
		mu 0 3 7 44 43
		f 3 103 104 -9
		mu 0 3 3 45 5
		f 3 -105 105 -101
		mu 0 3 5 45 44
		f 3 106 107 -104
		mu 0 3 3 46 45
		f 3 108 -107 -5
		mu 0 3 0 46 3
		f 3 109 110 -66
		mu 0 3 32 47 0
		f 3 -111 111 -109
		mu 0 3 0 47 46
		f 3 112 113 -110
		mu 0 3 32 48 47
		f 3 114 115 -68
		mu 0 3 33 49 32
		f 3 -116 116 -113
		mu 0 3 32 49 48
		f 3 117 118 -72
		mu 0 3 34 50 33
		f 3 -119 119 -115
		mu 0 3 33 50 49
		f 3 120 121 -118
		mu 0 3 34 51 50
		f 3 122 -121 -75
		mu 0 3 35 51 34
		f 3 123 124 -77
		mu 0 3 36 52 35
		f 3 -125 125 -123
		mu 0 3 35 52 51
		f 3 126 127 -81
		mu 0 3 37 53 36
		f 3 -128 128 -124
		mu 0 3 36 53 52
		f 3 129 130 -84
		mu 0 3 38 54 37
		f 3 -131 131 -127
		mu 0 3 37 54 53
		f 3 132 133 -130
		mu 0 3 38 55 54
		f 3 134 -133 -86
		mu 0 3 39 55 38
		f 3 135 -135 -91
		mu 0 3 40 55 39
		f 3 136 137 -94
		mu 0 3 41 56 40
		f 3 -138 138 -136
		mu 0 3 40 56 55
		f 3 139 140 -96
		mu 0 3 42 57 41
		f 3 -141 141 -137
		mu 0 3 41 57 56
		f 3 142 143 -140
		mu 0 3 42 58 57
		f 3 144 -143 -100
		mu 0 3 43 58 42
		f 3 145 146 -103
		mu 0 3 44 59 43
		f 3 -147 147 -145
		mu 0 3 43 59 58
		f 3 148 149 -106
		mu 0 3 45 60 44
		f 3 -150 150 -146
		mu 0 3 44 60 59
		f 3 151 152 -108
		mu 0 3 46 61 45
		f 3 -153 153 -149
		mu 0 3 45 61 60
		f 3 154 155 -152
		mu 0 3 46 62 61
		f 3 156 -155 -112
		mu 0 3 47 62 46
		f 3 157 158 -114
		mu 0 3 48 63 47
		f 3 -159 159 -157
		mu 0 3 47 63 62
		f 3 160 161 -158
		mu 0 3 48 64 63
		f 3 162 163 -117
		mu 0 3 49 65 48
		f 3 -164 164 -161
		mu 0 3 48 65 64
		f 3 165 166 -120
		mu 0 3 50 66 49
		f 3 -167 167 -163
		mu 0 3 49 66 65
		f 3 168 169 -166
		mu 0 3 50 67 66
		f 3 170 -169 -122
		mu 0 3 51 67 50
		f 3 171 172 -126
		mu 0 3 52 68 51
		f 3 -173 173 -171
		mu 0 3 51 68 67
		f 3 174 175 -129
		mu 0 3 53 69 52
		f 3 -176 176 -172
		mu 0 3 52 69 68
		f 3 177 178 -132
		mu 0 3 54 70 53
		f 3 -179 179 -175
		mu 0 3 53 70 69
		f 3 180 181 -178
		mu 0 3 54 71 70
		f 3 182 -181 -134
		mu 0 3 55 71 54
		f 3 183 -183 -139
		mu 0 3 56 71 55
		f 3 184 185 -142
		mu 0 3 57 72 56
		f 3 -186 186 -184
		mu 0 3 56 72 71
		f 3 187 188 -144
		mu 0 3 58 73 57
		f 3 -189 189 -185
		mu 0 3 57 73 72
		f 3 190 191 -188
		mu 0 3 58 74 73
		f 3 192 -191 -148
		mu 0 3 59 74 58
		f 3 193 194 -151
		mu 0 3 60 75 59
		f 3 -195 195 -193
		mu 0 3 59 75 74
		f 3 196 197 -154
		mu 0 3 61 76 60
		f 3 -198 198 -194
		mu 0 3 60 76 75
		f 3 199 200 -197
		mu 0 3 61 77 76
		f 3 201 -200 -156
		mu 0 3 62 77 61
		f 3 202 203 -160
		mu 0 3 63 78 62
		f 3 -204 204 -202
		mu 0 3 62 78 77
		f 3 205 206 -162
		mu 0 3 64 79 63
		f 3 -207 207 -203
		mu 0 3 63 79 78
		f 3 208 209 -206
		mu 0 3 64 80 79
		f 3 210 -209 -165
		mu 0 3 65 80 64
		f 3 211 -211 -168
		mu 0 3 66 80 65
		f 3 212 -212 -170
		mu 0 3 67 80 66
		f 3 213 -213 -174
		mu 0 3 68 80 67
		f 3 214 -214 -177
		mu 0 3 69 80 68
		f 3 215 -215 -180
		mu 0 3 70 80 69
		f 3 216 -216 -182
		mu 0 3 71 80 70
		f 3 217 -217 -187
		mu 0 3 72 80 71
		f 3 218 -218 -190
		mu 0 3 73 80 72
		f 3 219 -219 -192
		mu 0 3 74 80 73
		f 3 220 -220 -196
		mu 0 3 75 80 74
		f 3 221 -221 -199
		mu 0 3 76 80 75
		f 3 222 -222 -201
		mu 0 3 77 80 76
		f 3 223 -223 -205
		mu 0 3 78 80 77
		f 3 -208 -210 -224
		mu 0 3 78 79 80;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_52_SINGLE";
	rename -uid "00E9CD53-40C4-4E91-01A5-B8973B511F37";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_52_SINGLEShape" -p "Joint_1_Object_52_SINGLE";
	rename -uid "75931D5A-4E86-A260-E86F-E6A951FE8306";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_52_SINGLEShapeOrig" -p "Joint_1_Object_52_SINGLE";
	rename -uid "FB2E86D3-465E-9A2A-0679-FB88C6BCA3BD";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 81 ".uvst[0].uvsp[0:80]" -type "float2" 0.57421899 0.109375
		 0.59765601 0.0078119999 0.40234399 0.0078119999 0.71484399 0.167969 0.77734399 0.085937001
		 0.82031298 0.27734399 0.91406298 0.222656 0.87890601 0.421875 0.99218798 0.40234399
		 0.87890601 0.578125 0.99218798 0.59765601 0.82031298 0.72265601 0.91406298 0.77734399
		 0.71484399 0.83203101 0.77734399 0.91406298 0.57421899 0.890625 0.59765601 0.99218798
		 0.42578101 0.890625 0.40234399 0.99218798 0.28515601 0.83203101 0.222656 0.91406298
		 0.17968801 0.72265601 0.085937001 0.77734399 0.121094 0.578125 0.0078119999 0.59765601
		 0.121094 0.421875 0.0078119999 0.40234399 0.17968801 0.27734399 0.085937001 0.222656
		 0.28515601 0.167969 0.222656 0.085937001 0.42578101 0.109375 0.44140601 0.183594
		 0.328125 0.234375 0.246094 0.32031301 0.199219 0.4375 0.199219 0.5625 0.246094 0.67968798
		 0.328125 0.765625 0.44140601 0.81640601 0.55859399 0.81640601 0.671875 0.765625 0.75390601
		 0.67968798 0.80078101 0.5625 0.80078101 0.4375 0.75390601 0.32031301 0.671875 0.234375
		 0.55859399 0.183594 0.46093801 0.28906301 0.38281301 0.32031301 0.32421899 0.37890601
		 0.29296899 0.45703101 0.29296899 0.54296899 0.32421899 0.62109399 0.38281301 0.67968798
		 0.46093801 0.71093798 0.53906298 0.71093798 0.61718798 0.67968798 0.67578101 0.62109399
		 0.70703101 0.54296899 0.70703101 0.45703101 0.67578101 0.37890601 0.61718798 0.32031301
		 0.53906298 0.28906301 0.48046899 0.390625 0.44140601 0.40625 0.41015601 0.4375 0.39453101
		 0.47656301 0.39453101 0.52343798 0.41015601 0.5625 0.44140601 0.59375 0.48046899
		 0.609375 0.51953101 0.609375 0.55859399 0.59375 0.58984399 0.5625 0.60546899 0.52343798
		 0.60546899 0.47656301 0.58984399 0.4375 0.55859399 0.40625 0.51953101 0.390625 0.5
		 0.5;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 81 ".vt[0:80]"  4.26732016 7.84907007 -3.93033004 4.86326981 7.85674 -4.58925009
		 4.68876982 8.017560005 -4.74020004 4.37334013 7.62510014 -3.83298993 4.97539997 7.61743021 -4.48620987
		 4.40289021 7.36962986 -3.79727006 5.0074601173 7.34021997 -4.44744015 4.35461998 7.11304998 -3.82560992
		 4.95326996 7.059949875 -4.47960997 4.23257017 6.89532995 -3.91649008 4.82402992 6.8294301 -4.57582998
		 4.058269978 6.75489998 -4.053850174 4.63411999 6.67425013 -4.72540998 3.8599999 6.70940018 -4.21519995
		 4.41898012 6.62487984 -4.90048981 3.66065001 6.76688004 -4.38202 4.20633984 6.68489981 -5.078370094
		 3.49826002 6.91654015 -4.52249002 4.031839848 6.84571981 -5.22932005 3.39467001 7.13827991 -4.61773014
		 3.91970992 7.085030079 -5.3323698 3.36269999 7.39597988 -4.65555 3.88765001 7.36223984 -5.37112999
		 3.41096997 7.65256977 -4.62720013 3.94183993 7.64250994 -5.33896017 3.53302002 7.87027979 -4.53633022
		 4.071070194 7.87303019 -5.24274015 3.70731997 8.010720253 -4.39896011 4.26099014 8.028209686 -5.093160152
		 3.90801001 8.053979874 -4.23551989 4.47613001 8.077580452 -4.91808987 4.10493994 7.99873018 -4.070789814
		 3.74537992 7.94708014 -3.68106008 3.57322001 7.99406004 -3.82501006 3.39846992 7.95116997 -3.96708989
		 3.24642992 7.82422018 -4.08671999 3.13874006 7.63211012 -4.16690016 3.09333992 7.40686989 -4.19427013
		 3.11732006 7.18081999 -4.16445017 3.20690989 6.98654985 -4.081970215 3.34991002 6.85476017 -3.95828009
		 3.52205992 6.80777979 -3.8143301 3.69682002 6.85066986 -3.67224002 3.85127997 6.97538996 -3.55051994
		 3.95897007 7.16750002 -3.47034001 4.0019497871 7.39496994 -3.44506001 3.97796988 7.62102985 -3.47488999
		 3.88838005 7.81528997 -3.55735993 3.4444499 7.82777023 -3.40207005 3.31456995 7.86492014 -3.51074004
		 3.17956996 7.83394003 -3.62058997 3.06298995 7.73744011 -3.71235991 2.98042011 7.59015989 -3.77383995
		 2.94623995 7.41771984 -3.79432011 2.96636009 7.24378014 -3.76999998 3.035209894 7.097770214 -3.70675993
		 3.14184999 6.99947977 -3.61452007 3.27172995 6.96232986 -3.50584006 3.40429997 6.99554014 -3.39808011
		 3.52089 7.092040062 -3.30631995 3.60345006 7.2393198 -3.24483991 3.63764 7.41176987 -3.22434998
		 3.61994004 7.58346987 -3.24657989 3.55109 7.72947979 -3.30981994 3.20142007 7.62524986 -3.26411009
		 3.1361599 7.64654016 -3.31883001 3.068670034 7.63105011 -3.37374997 3.013380051 7.58488989 -3.41724992
		 2.97389007 7.51445007 -3.44665003 2.95738006 7.43254995 -3.45660996 2.96743989 7.3455801 -3.4444499
		 3.0039799213 7.27305984 -3.41110992 3.059720039 7.22168016 -3.36289001 3.12497997 7.20038986 -3.30817008
		 3.19247007 7.2158699 -3.25324988 3.25018001 7.25979996 -3.20764995 3.28966999 7.33023977 -3.17825007
		 3.30376005 7.41438007 -3.17038989 3.29369998 7.50134993 -3.18254995 3.25715995 7.57387018 -3.21588993
		 3.07468009 7.42542982 -3.24316001;
	setAttr -s 224 ".ed";
	setAttr ".ed[0:165]"  0 1 1 1 2 0 2 0 1 3 1 1 0 3 1 3 4 1 4 1 0 5 4 1 3 5 1
		 5 6 1 6 4 0 7 6 1 5 7 1 7 8 1 8 6 0 9 8 1 7 9 1 9 10 1 10 8 0 11 10 1 9 11 1 11 12 1
		 12 10 0 13 12 1 11 13 1 13 14 1 14 12 0 15 14 1 13 15 1 15 16 1 16 14 0 17 16 1 15 17 1
		 17 18 1 18 16 0 19 18 1 17 19 1 19 20 1 20 18 0 21 20 1 19 21 1 21 22 1 22 20 0 23 22 1
		 21 23 1 23 24 1 24 22 0 25 24 1 23 25 1 25 26 1 26 24 0 27 26 1 25 27 1 27 28 1 28 26 0
		 29 28 1 27 29 1 29 30 1 30 28 0 31 2 1 2 30 0 30 31 1 31 0 1 29 31 1 31 32 1 32 0 1
		 29 33 1 33 31 1 33 32 1 29 34 1 34 33 1 27 34 1 25 35 1 35 27 1 35 34 1 23 36 1 36 25 1
		 36 35 1 21 37 1 37 23 1 37 36 1 21 38 1 38 37 1 19 38 1 17 39 1 39 19 1 15 39 1 39 38 1
		 13 40 1 40 15 1 40 39 1 11 41 1 41 13 1 41 40 1 11 42 1 42 41 1 9 42 1 7 43 1 43 9 1
		 43 42 1 5 44 1 44 7 1 44 43 1 3 45 1 45 5 1 45 44 1 3 46 1 46 45 1 0 46 1 32 47 1
		 47 0 1 47 46 1 32 48 1 48 47 1 33 49 1 49 32 1 49 48 1 33 50 1 50 49 1 34 50 1 35 51 1
		 51 34 1 51 50 1 36 52 1 52 35 1 52 51 1 37 53 1 53 36 1 53 52 1 37 54 1 54 53 1 38 54 1
		 39 55 1 55 38 1 40 55 1 55 54 1 41 56 1 56 40 1 56 55 1 42 57 1 57 41 1 57 56 1 42 58 1
		 58 57 1 43 58 1 44 59 1 59 43 1 59 58 1 45 60 1 60 44 1 60 59 1 46 61 1 61 45 1 61 60 1
		 46 62 1 62 61 1 47 62 1 48 63 1 63 47 1 63 62 1 48 64 1 64 63 1 49 65 1 65 48 1 65 64 1
		 49 66 1;
	setAttr ".ed[166:223]" 66 65 1 50 66 1 51 67 1 67 50 1 67 66 1 52 68 1 68 51 1
		 68 67 1 53 69 1 69 52 1 69 68 1 53 70 1 70 69 1 54 70 1 55 71 1 71 54 1 56 71 1 71 70 1
		 57 72 1 72 56 1 72 71 1 57 73 1 73 72 1 58 73 1 59 74 1 74 58 1 74 73 1 60 75 1 75 59 1
		 75 74 1 61 76 1 76 60 1 76 75 1 61 77 1 77 76 1 62 77 1 63 78 1 78 62 1 78 77 1 64 79 1
		 79 63 1 79 78 1 64 80 1 80 79 1 65 80 1 66 80 1 67 80 1 68 80 1 69 80 1 70 80 1 71 80 1
		 72 80 1 73 80 1 74 80 1 75 80 1 76 80 1 77 80 1 78 80 1;
	setAttr -s 81 ".n[0:80]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 144 -ch 432 ".fc[0:143]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 -1 4
		mu 0 3 3 1 0
		f 3 5 6 -4
		mu 0 3 3 4 1
		f 3 7 -6 8
		mu 0 3 5 4 3
		f 3 9 10 -8
		mu 0 3 5 6 4
		f 3 11 -10 12
		mu 0 3 7 6 5
		f 3 13 14 -12
		mu 0 3 7 8 6
		f 3 15 -14 16
		mu 0 3 9 8 7
		f 3 17 18 -16
		mu 0 3 9 10 8
		f 3 19 -18 20
		mu 0 3 11 10 9
		f 3 21 22 -20
		mu 0 3 11 12 10
		f 3 23 -22 24
		mu 0 3 13 12 11
		f 3 25 26 -24
		mu 0 3 13 14 12
		f 3 27 -26 28
		mu 0 3 15 14 13
		f 3 29 30 -28
		mu 0 3 15 16 14
		f 3 31 -30 32
		mu 0 3 17 16 15
		f 3 33 34 -32
		mu 0 3 17 18 16
		f 3 35 -34 36
		mu 0 3 19 18 17
		f 3 37 38 -36
		mu 0 3 19 20 18
		f 3 39 -38 40
		mu 0 3 21 20 19
		f 3 41 42 -40
		mu 0 3 21 22 20
		f 3 43 -42 44
		mu 0 3 23 22 21
		f 3 45 46 -44
		mu 0 3 23 24 22
		f 3 47 -46 48
		mu 0 3 25 24 23
		f 3 49 50 -48
		mu 0 3 25 26 24
		f 3 51 -50 52
		mu 0 3 27 26 25
		f 3 53 54 -52
		mu 0 3 27 28 26
		f 3 55 -54 56
		mu 0 3 29 28 27
		f 3 57 58 -56
		mu 0 3 29 30 28
		f 3 59 60 61
		mu 0 3 31 2 30
		f 3 62 -3 -60
		mu 0 3 31 0 2
		f 3 -62 -58 63
		mu 0 3 31 30 29
		f 3 64 65 -63
		mu 0 3 31 32 0
		f 3 66 67 -64
		mu 0 3 29 33 31
		f 3 -68 68 -65
		mu 0 3 31 33 32
		f 3 69 70 -67
		mu 0 3 29 34 33
		f 3 71 -70 -57
		mu 0 3 27 34 29
		f 3 72 73 -53
		mu 0 3 25 35 27
		f 3 -74 74 -72
		mu 0 3 27 35 34
		f 3 75 76 -49
		mu 0 3 23 36 25
		f 3 -77 77 -73
		mu 0 3 25 36 35
		f 3 78 79 -45
		mu 0 3 21 37 23
		f 3 -80 80 -76
		mu 0 3 23 37 36
		f 3 81 82 -79
		mu 0 3 21 38 37
		f 3 83 -82 -41
		mu 0 3 19 38 21
		f 3 84 85 -37
		mu 0 3 17 39 19
		f 3 86 -85 -33
		mu 0 3 15 39 17
		f 3 -86 87 -84
		mu 0 3 19 39 38
		f 3 88 89 -29
		mu 0 3 13 40 15
		f 3 -90 90 -87
		mu 0 3 15 40 39
		f 3 91 92 -25
		mu 0 3 11 41 13
		f 3 -93 93 -89
		mu 0 3 13 41 40
		f 3 94 95 -92
		mu 0 3 11 42 41
		f 3 96 -95 -21
		mu 0 3 9 42 11
		f 3 97 98 -17
		mu 0 3 7 43 9
		f 3 -99 99 -97
		mu 0 3 9 43 42
		f 3 100 101 -13
		mu 0 3 5 44 7
		f 3 -102 102 -98
		mu 0 3 7 44 43
		f 3 103 104 -9
		mu 0 3 3 45 5
		f 3 -105 105 -101
		mu 0 3 5 45 44
		f 3 106 107 -104
		mu 0 3 3 46 45
		f 3 108 -107 -5
		mu 0 3 0 46 3
		f 3 109 110 -66
		mu 0 3 32 47 0
		f 3 -111 111 -109
		mu 0 3 0 47 46
		f 3 112 113 -110
		mu 0 3 32 48 47
		f 3 114 115 -69
		mu 0 3 33 49 32
		f 3 -116 116 -113
		mu 0 3 32 49 48
		f 3 117 118 -115
		mu 0 3 33 50 49
		f 3 119 -118 -71
		mu 0 3 34 50 33
		f 3 120 121 -75
		mu 0 3 35 51 34
		f 3 -122 122 -120
		mu 0 3 34 51 50
		f 3 123 124 -78
		mu 0 3 36 52 35
		f 3 -125 125 -121
		mu 0 3 35 52 51
		f 3 126 127 -81
		mu 0 3 37 53 36
		f 3 -128 128 -124
		mu 0 3 36 53 52
		f 3 129 130 -127
		mu 0 3 37 54 53
		f 3 131 -130 -83
		mu 0 3 38 54 37
		f 3 132 133 -88
		mu 0 3 39 55 38
		f 3 134 -133 -91
		mu 0 3 40 55 39
		f 3 -134 135 -132
		mu 0 3 38 55 54
		f 3 136 137 -94
		mu 0 3 41 56 40
		f 3 -138 138 -135
		mu 0 3 40 56 55
		f 3 139 140 -96
		mu 0 3 42 57 41
		f 3 -141 141 -137
		mu 0 3 41 57 56
		f 3 142 143 -140
		mu 0 3 42 58 57
		f 3 144 -143 -100
		mu 0 3 43 58 42
		f 3 145 146 -103
		mu 0 3 44 59 43
		f 3 -147 147 -145
		mu 0 3 43 59 58
		f 3 148 149 -106
		mu 0 3 45 60 44
		f 3 -150 150 -146
		mu 0 3 44 60 59
		f 3 151 152 -108
		mu 0 3 46 61 45
		f 3 -153 153 -149
		mu 0 3 45 61 60
		f 3 154 155 -152
		mu 0 3 46 62 61
		f 3 156 -155 -112
		mu 0 3 47 62 46
		f 3 157 158 -114
		mu 0 3 48 63 47
		f 3 -159 159 -157
		mu 0 3 47 63 62
		f 3 160 161 -158
		mu 0 3 48 64 63
		f 3 162 163 -117
		mu 0 3 49 65 48
		f 3 -164 164 -161
		mu 0 3 48 65 64
		f 3 165 166 -163
		mu 0 3 49 66 65
		f 3 167 -166 -119
		mu 0 3 50 66 49
		f 3 168 169 -123
		mu 0 3 51 67 50
		f 3 -170 170 -168
		mu 0 3 50 67 66
		f 3 171 172 -126
		mu 0 3 52 68 51
		f 3 -173 173 -169
		mu 0 3 51 68 67
		f 3 174 175 -129
		mu 0 3 53 69 52
		f 3 -176 176 -172
		mu 0 3 52 69 68
		f 3 177 178 -175
		mu 0 3 53 70 69
		f 3 179 -178 -131
		mu 0 3 54 70 53
		f 3 180 181 -136
		mu 0 3 55 71 54
		f 3 182 -181 -139
		mu 0 3 56 71 55
		f 3 -182 183 -180
		mu 0 3 54 71 70
		f 3 184 185 -142
		mu 0 3 57 72 56
		f 3 -186 186 -183
		mu 0 3 56 72 71
		f 3 187 188 -185
		mu 0 3 57 73 72
		f 3 189 -188 -144
		mu 0 3 58 73 57
		f 3 190 191 -148
		mu 0 3 59 74 58
		f 3 -192 192 -190
		mu 0 3 58 74 73
		f 3 193 194 -151
		mu 0 3 60 75 59
		f 3 -195 195 -191
		mu 0 3 59 75 74
		f 3 196 197 -154
		mu 0 3 61 76 60
		f 3 -198 198 -194
		mu 0 3 60 76 75
		f 3 199 200 -197
		mu 0 3 61 77 76
		f 3 201 -200 -156
		mu 0 3 62 77 61
		f 3 202 203 -160
		mu 0 3 63 78 62
		f 3 -204 204 -202
		mu 0 3 62 78 77
		f 3 205 206 -162
		mu 0 3 64 79 63
		f 3 -207 207 -203
		mu 0 3 63 79 78
		f 3 208 209 -206
		mu 0 3 64 80 79
		f 3 210 -209 -165
		mu 0 3 65 80 64
		f 3 211 -211 -167
		mu 0 3 66 80 65
		f 3 212 -212 -171
		mu 0 3 67 80 66
		f 3 213 -213 -174
		mu 0 3 68 80 67
		f 3 214 -214 -177
		mu 0 3 69 80 68
		f 3 215 -215 -179
		mu 0 3 70 80 69
		f 3 216 -216 -184
		mu 0 3 71 80 70
		f 3 217 -217 -187
		mu 0 3 72 80 71
		f 3 218 -218 -189
		mu 0 3 73 80 72
		f 3 219 -219 -193
		mu 0 3 74 80 73
		f 3 220 -220 -196
		mu 0 3 75 80 74
		f 3 221 -221 -199
		mu 0 3 76 80 75
		f 3 222 -222 -201
		mu 0 3 77 80 76
		f 3 223 -223 -205
		mu 0 3 78 80 77
		f 3 -208 -210 -224
		mu 0 3 78 79 80;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode transform -n "Joint_1_Object_53_SINGLE";
	rename -uid "4C5CC79C-44D6-114B-3080-F192D757A2F0";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "Joint_1_Object_53_SINGLEShape" -p "Joint_1_Object_53_SINGLE";
	rename -uid "B11A6799-45DD-35D1-DD2F-6E941BF64C14";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".vcs" 2;
createNode mesh -n "Joint_1_Object_53_SINGLEShapeOrig" -p "Joint_1_Object_53_SINGLE";
	rename -uid "678C8874-4DC0-CECA-CDE6-3CB8A87E0CAB";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 81 ".uvst[0].uvsp[0:80]" -type "float2" 0.57421899 0.109375
		 0.59765601 0.0078119999 0.40234399 0.0078119999 0.71484399 0.167969 0.77734399 0.085937001
		 0.82031298 0.27734399 0.91406298 0.222656 0.87890601 0.421875 0.99218798 0.40234399
		 0.87890601 0.578125 0.99218798 0.59765601 0.82031298 0.72265601 0.91406298 0.77734399
		 0.71484399 0.83203101 0.77734399 0.91406298 0.57421899 0.890625 0.59765601 0.99218798
		 0.42578101 0.890625 0.40234399 0.99218798 0.28515601 0.83203101 0.222656 0.91406298
		 0.17968801 0.72265601 0.085937001 0.77734399 0.121094 0.578125 0.0078119999 0.59765601
		 0.121094 0.421875 0.0078119999 0.40234399 0.17968801 0.27734399 0.085937001 0.222656
		 0.28515601 0.167969 0.222656 0.085937001 0.42578101 0.109375 0.44140601 0.183594
		 0.328125 0.234375 0.246094 0.32031301 0.199219 0.4375 0.199219 0.5625 0.246094 0.67968798
		 0.328125 0.765625 0.44140601 0.81640601 0.55859399 0.81640601 0.671875 0.765625 0.75390601
		 0.67968798 0.80078101 0.5625 0.80078101 0.4375 0.75390601 0.32031301 0.671875 0.234375
		 0.55859399 0.183594 0.46093801 0.28906301 0.38281301 0.32031301 0.32421899 0.37890601
		 0.29296899 0.45703101 0.29296899 0.54296899 0.32421899 0.62109399 0.38281301 0.67968798
		 0.46093801 0.71093798 0.53906298 0.71093798 0.61718798 0.67968798 0.67578101 0.62109399
		 0.70703101 0.54296899 0.70703101 0.45703101 0.67578101 0.37890601 0.61718798 0.32031301
		 0.53906298 0.28906301 0.48046899 0.390625 0.44140601 0.40625 0.41015601 0.4375 0.39453101
		 0.47656301 0.39453101 0.52343798 0.41015601 0.5625 0.44140601 0.59375 0.48046899
		 0.609375 0.51953101 0.609375 0.55859399 0.59375 0.58984399 0.5625 0.60546899 0.52343798
		 0.60546899 0.47656301 0.58984399 0.4375 0.55859399 0.40625 0.51953101 0.390625 0.5
		 0.5;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr -s 81 ".vt[0:80]"  3.40850997 7.21884012 -4.63523006 3.9995501 7.22886992 -5.29324007
		 3.82505012 7.38969994 -5.44419003 3.51210999 6.99709988 -4.53998995 4.11168003 6.98956013 -5.19019985
		 3.54228997 6.73619986 -4.50351 4.14195013 6.70914984 -5.15277004 3.49159002 6.48185015 -4.53394985
		 4.089550018 6.43208981 -5.18359995 3.37133002 6.26733017 -4.62348986 3.95851994 6.19835997 -5.28115988
		 3.19946003 6.12467003 -4.75875998 3.77040005 6.046390057 -5.42939997 2.99696994 6.078199863 -4.92354012
		 3.55345988 5.99382019 -5.60581017 2.80004001 6.13345003 -5.088260174 3.34082007 6.053830147 -5.78369999
		 2.63523006 6.28533983 -5.23083019 3.16632009 6.21466017 -5.93463993 2.53164005 6.50708008 -5.32606983
		 3.054199934 6.45396996 -6.037690163 2.50146008 6.7679801 -5.36254978 3.023930073 6.73437977 -6.075119972
		 2.55215001 7.022339821 -5.33210993 3.076329947 7.0114398 -6.044290066 2.67241001 7.23684978 -5.24256992
		 3.20736003 7.24517012 -5.94673014 2.84429002 7.37951994 -5.1072998 3.39547992 7.39714003 -5.79849005
		 3.046780109 7.42598009 -4.94252014 3.61241007 7.44970989 -5.62207985 3.24371004 7.37073994 -4.77779007
		 2.88477993 7.31365013 -4.38730001 2.71441007 7.36383009 -4.52991009 2.53543997 7.31997013 -4.67542982
		 2.38339996 7.19301987 -4.79505014 2.27749991 7.0041098595 -4.87389994 2.23210001 6.77888012 -4.90127993
		 2.25671005 6.54737997 -4.87068987 2.34809995 6.3563199 -4.78688002 2.48867011 6.22676992 -4.66527987
		 2.65902996 6.17657995 -4.52266979 2.83801007 6.22043991 -4.37715006 2.99004006 6.34740019 -4.25753021
		 3.095940113 6.53630018 -4.17867994 3.14134002 6.76153994 -4.15129995 3.11672997 6.99303007 -4.18189001
		 3.025350094 7.18409014 -4.26569986 2.58072996 7.19990015 -4.10605001 2.44904995 7.23386002 -4.21607018
		 2.31405997 7.20287991 -4.3259201 2.19747996 7.10637999 -4.4176898 2.11669993 6.96229982 -4.47782993
		 2.082520008 6.78985023 -4.49831009 2.10263991 6.61592007 -4.47398996 2.16969991 6.46670008 -4.41208982
		 2.27634001 6.36842012 -4.31983995 2.40801001 6.3344698 -4.20982981 2.54301 6.36543989 -4.099979877
		 2.65959001 6.46193981 -4.0082101822 2.74036002 6.60601997 -3.94807005 2.77454996 6.77847004 -3.92758012
		 2.75443006 6.95241022 -3.95191002 2.68737006 7.1016202 -4.013810158 2.34012008 6.99515009 -3.96600008
		 2.2730701 7.013239861 -4.022059917 2.20737004 7.0009598732 -4.075650215 2.14787006 6.95382977 -4.12258005
		 2.11016989 6.88659 -4.15064001 2.094290018 6.79925013 -4.15984011 2.10614991 6.71547985 -4.14633989
		 2.14088988 6.63976002 -4.11433983 2.19421005 6.59062004 -4.068220139 2.26126003 6.57251978 -4.012159824
		 2.32696009 6.58480978 -3.95857 2.38646007 6.63193989 -3.91163993 2.42416 6.69918013 -3.88357997
		 2.44004011 6.78652 -3.87438011 2.42817998 6.8702898 -3.88788009 2.39344001 6.94601011 -3.91987991
		 2.21164989 6.79422998 -3.95148993;
	setAttr -s 224 ".ed";
	setAttr ".ed[0:165]"  0 1 1 1 2 0 2 0 1 3 1 1 0 3 1 3 4 1 4 1 0 5 4 1 3 5 1
		 5 6 1 6 4 0 7 6 1 5 7 1 7 8 1 8 6 0 9 8 1 7 9 1 9 10 1 10 8 0 11 10 1 9 11 1 11 12 1
		 12 10 0 13 12 1 11 13 1 13 14 1 14 12 0 15 14 1 13 15 1 15 16 1 16 14 0 17 16 1 15 17 1
		 17 18 1 18 16 0 19 18 1 17 19 1 19 20 1 20 18 0 21 20 1 19 21 1 21 22 1 22 20 0 23 22 1
		 21 23 1 23 24 1 24 22 0 25 24 1 23 25 1 25 26 1 26 24 0 27 26 1 25 27 1 27 28 1 28 26 0
		 29 28 1 27 29 1 29 30 1 30 28 0 31 2 1 2 30 0 30 31 1 31 0 1 29 31 1 31 32 1 32 0 1
		 31 33 1 33 32 1 29 33 1 27 34 1 34 29 1 34 33 1 25 35 1 35 27 1 35 34 1 23 36 1 36 25 1
		 36 35 1 23 37 1 37 36 1 21 37 1 19 38 1 38 21 1 38 37 1 17 39 1 39 19 1 15 39 1 39 38 1
		 15 40 1 40 39 1 13 40 1 11 41 1 41 13 1 41 40 1 9 42 1 42 11 1 42 41 1 7 43 1 43 9 1
		 43 42 1 7 44 1 44 43 1 5 44 1 3 45 1 45 5 1 45 44 1 0 46 1 46 3 1 46 45 1 32 47 1
		 47 0 1 47 46 1 32 48 1 48 47 1 32 49 1 49 48 1 33 49 1 34 50 1 50 33 1 50 49 1 35 51 1
		 51 34 1 51 50 1 36 52 1 52 35 1 52 51 1 36 53 1 53 52 1 37 53 1 38 54 1 54 37 1 54 53 1
		 39 55 1 55 38 1 40 55 1 55 54 1 40 56 1 56 55 1 41 56 1 42 57 1 57 41 1 57 56 1 43 58 1
		 58 42 1 58 57 1 44 59 1 59 43 1 59 58 1 44 60 1 60 59 1 45 60 1 46 61 1 61 45 1 61 60 1
		 47 62 1 62 46 1 62 61 1 48 63 1 63 47 1 63 62 1 48 64 1 64 63 1 48 65 1 65 64 1 49 65 1
		 50 66 1;
	setAttr ".ed[166:223]" 66 49 1 66 65 1 51 67 1 67 50 1 67 66 1 52 68 1 68 51 1
		 68 67 1 52 69 1 69 68 1 53 69 1 54 70 1 70 53 1 70 69 1 55 71 1 71 54 1 56 71 1 71 70 1
		 56 72 1 72 71 1 57 72 1 58 73 1 73 57 1 73 72 1 59 74 1 74 58 1 74 73 1 60 75 1 75 59 1
		 75 74 1 60 76 1 76 75 1 61 76 1 62 77 1 77 61 1 77 76 1 63 78 1 78 62 1 78 77 1 64 79 1
		 79 63 1 79 78 1 64 80 1 80 79 1 65 80 1 66 80 1 67 80 1 68 80 1 69 80 1 70 80 1 71 80 1
		 72 80 1 73 80 1 74 80 1 75 80 1 76 80 1 77 80 1 78 80 1;
	setAttr -s 81 ".n[0:80]" -type "float3"  1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20
		 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20 1e+20;
	setAttr -s 144 -ch 432 ".fc[0:143]" -type "polyFaces" 
		f 3 0 1 2
		mu 0 3 0 1 2
		f 3 3 -1 4
		mu 0 3 3 1 0
		f 3 5 6 -4
		mu 0 3 3 4 1
		f 3 7 -6 8
		mu 0 3 5 4 3
		f 3 9 10 -8
		mu 0 3 5 6 4
		f 3 11 -10 12
		mu 0 3 7 6 5
		f 3 13 14 -12
		mu 0 3 7 8 6
		f 3 15 -14 16
		mu 0 3 9 8 7
		f 3 17 18 -16
		mu 0 3 9 10 8
		f 3 19 -18 20
		mu 0 3 11 10 9
		f 3 21 22 -20
		mu 0 3 11 12 10
		f 3 23 -22 24
		mu 0 3 13 12 11
		f 3 25 26 -24
		mu 0 3 13 14 12
		f 3 27 -26 28
		mu 0 3 15 14 13
		f 3 29 30 -28
		mu 0 3 15 16 14
		f 3 31 -30 32
		mu 0 3 17 16 15
		f 3 33 34 -32
		mu 0 3 17 18 16
		f 3 35 -34 36
		mu 0 3 19 18 17
		f 3 37 38 -36
		mu 0 3 19 20 18
		f 3 39 -38 40
		mu 0 3 21 20 19
		f 3 41 42 -40
		mu 0 3 21 22 20
		f 3 43 -42 44
		mu 0 3 23 22 21
		f 3 45 46 -44
		mu 0 3 23 24 22
		f 3 47 -46 48
		mu 0 3 25 24 23
		f 3 49 50 -48
		mu 0 3 25 26 24
		f 3 51 -50 52
		mu 0 3 27 26 25
		f 3 53 54 -52
		mu 0 3 27 28 26
		f 3 55 -54 56
		mu 0 3 29 28 27
		f 3 57 58 -56
		mu 0 3 29 30 28
		f 3 59 60 61
		mu 0 3 31 2 30
		f 3 62 -3 -60
		mu 0 3 31 0 2
		f 3 -62 -58 63
		mu 0 3 31 30 29
		f 3 64 65 -63
		mu 0 3 31 32 0
		f 3 66 67 -65
		mu 0 3 31 33 32
		f 3 68 -67 -64
		mu 0 3 29 33 31
		f 3 69 70 -57
		mu 0 3 27 34 29
		f 3 -71 71 -69
		mu 0 3 29 34 33
		f 3 72 73 -53
		mu 0 3 25 35 27
		f 3 -74 74 -70
		mu 0 3 27 35 34
		f 3 75 76 -49
		mu 0 3 23 36 25
		f 3 -77 77 -73
		mu 0 3 25 36 35
		f 3 78 79 -76
		mu 0 3 23 37 36
		f 3 80 -79 -45
		mu 0 3 21 37 23
		f 3 81 82 -41
		mu 0 3 19 38 21
		f 3 -83 83 -81
		mu 0 3 21 38 37
		f 3 84 85 -37
		mu 0 3 17 39 19
		f 3 86 -85 -33
		mu 0 3 15 39 17
		f 3 -86 87 -82
		mu 0 3 19 39 38
		f 3 88 89 -87
		mu 0 3 15 40 39
		f 3 90 -89 -29
		mu 0 3 13 40 15
		f 3 91 92 -25
		mu 0 3 11 41 13
		f 3 -93 93 -91
		mu 0 3 13 41 40
		f 3 94 95 -21
		mu 0 3 9 42 11
		f 3 -96 96 -92
		mu 0 3 11 42 41
		f 3 97 98 -17
		mu 0 3 7 43 9
		f 3 -99 99 -95
		mu 0 3 9 43 42
		f 3 100 101 -98
		mu 0 3 7 44 43
		f 3 102 -101 -13
		mu 0 3 5 44 7
		f 3 103 104 -9
		mu 0 3 3 45 5
		f 3 -105 105 -103
		mu 0 3 5 45 44
		f 3 106 107 -5
		mu 0 3 0 46 3
		f 3 -108 108 -104
		mu 0 3 3 46 45
		f 3 109 110 -66
		mu 0 3 32 47 0
		f 3 -111 111 -107
		mu 0 3 0 47 46
		f 3 112 113 -110
		mu 0 3 32 48 47
		f 3 114 115 -113
		mu 0 3 32 49 48
		f 3 116 -115 -68
		mu 0 3 33 49 32
		f 3 117 118 -72
		mu 0 3 34 50 33
		f 3 -119 119 -117
		mu 0 3 33 50 49
		f 3 120 121 -75
		mu 0 3 35 51 34
		f 3 -122 122 -118
		mu 0 3 34 51 50
		f 3 123 124 -78
		mu 0 3 36 52 35
		f 3 -125 125 -121
		mu 0 3 35 52 51
		f 3 126 127 -124
		mu 0 3 36 53 52
		f 3 128 -127 -80
		mu 0 3 37 53 36
		f 3 129 130 -84
		mu 0 3 38 54 37
		f 3 -131 131 -129
		mu 0 3 37 54 53
		f 3 132 133 -88
		mu 0 3 39 55 38
		f 3 134 -133 -90
		mu 0 3 40 55 39
		f 3 -134 135 -130
		mu 0 3 38 55 54
		f 3 136 137 -135
		mu 0 3 40 56 55
		f 3 138 -137 -94
		mu 0 3 41 56 40
		f 3 139 140 -97
		mu 0 3 42 57 41
		f 3 -141 141 -139
		mu 0 3 41 57 56
		f 3 142 143 -100
		mu 0 3 43 58 42
		f 3 -144 144 -140
		mu 0 3 42 58 57
		f 3 145 146 -102
		mu 0 3 44 59 43
		f 3 -147 147 -143
		mu 0 3 43 59 58
		f 3 148 149 -146
		mu 0 3 44 60 59
		f 3 150 -149 -106
		mu 0 3 45 60 44
		f 3 151 152 -109
		mu 0 3 46 61 45
		f 3 -153 153 -151
		mu 0 3 45 61 60
		f 3 154 155 -112
		mu 0 3 47 62 46
		f 3 -156 156 -152
		mu 0 3 46 62 61
		f 3 157 158 -114
		mu 0 3 48 63 47
		f 3 -159 159 -155
		mu 0 3 47 63 62
		f 3 160 161 -158
		mu 0 3 48 64 63
		f 3 162 163 -161
		mu 0 3 48 65 64
		f 3 164 -163 -116
		mu 0 3 49 65 48
		f 3 165 166 -120
		mu 0 3 50 66 49
		f 3 -167 167 -165
		mu 0 3 49 66 65
		f 3 168 169 -123
		mu 0 3 51 67 50
		f 3 -170 170 -166
		mu 0 3 50 67 66
		f 3 171 172 -126
		mu 0 3 52 68 51
		f 3 -173 173 -169
		mu 0 3 51 68 67
		f 3 174 175 -172
		mu 0 3 52 69 68
		f 3 176 -175 -128
		mu 0 3 53 69 52
		f 3 177 178 -132
		mu 0 3 54 70 53
		f 3 -179 179 -177
		mu 0 3 53 70 69
		f 3 180 181 -136
		mu 0 3 55 71 54
		f 3 182 -181 -138
		mu 0 3 56 71 55
		f 3 -182 183 -178
		mu 0 3 54 71 70
		f 3 184 185 -183
		mu 0 3 56 72 71
		f 3 186 -185 -142
		mu 0 3 57 72 56
		f 3 187 188 -145
		mu 0 3 58 73 57
		f 3 -189 189 -187
		mu 0 3 57 73 72
		f 3 190 191 -148
		mu 0 3 59 74 58
		f 3 -192 192 -188
		mu 0 3 58 74 73
		f 3 193 194 -150
		mu 0 3 60 75 59
		f 3 -195 195 -191
		mu 0 3 59 75 74
		f 3 196 197 -194
		mu 0 3 60 76 75
		f 3 198 -197 -154
		mu 0 3 61 76 60
		f 3 199 200 -157
		mu 0 3 62 77 61
		f 3 -201 201 -199
		mu 0 3 61 77 76
		f 3 202 203 -160
		mu 0 3 63 78 62
		f 3 -204 204 -200
		mu 0 3 62 78 77
		f 3 205 206 -162
		mu 0 3 64 79 63
		f 3 -207 207 -203
		mu 0 3 63 79 78
		f 3 208 209 -206
		mu 0 3 64 80 79
		f 3 210 -209 -164
		mu 0 3 65 80 64
		f 3 211 -211 -168
		mu 0 3 66 80 65
		f 3 212 -212 -171
		mu 0 3 67 80 66
		f 3 213 -213 -174
		mu 0 3 68 80 67
		f 3 214 -214 -176
		mu 0 3 69 80 68
		f 3 215 -215 -180
		mu 0 3 70 80 69
		f 3 216 -216 -184
		mu 0 3 71 80 70
		f 3 217 -217 -186
		mu 0 3 72 80 71
		f 3 218 -218 -190
		mu 0 3 73 80 72
		f 3 219 -219 -193
		mu 0 3 74 80 73
		f 3 220 -220 -196
		mu 0 3 75 80 74
		f 3 221 -221 -198
		mu 0 3 76 80 75
		f 3 222 -222 -202
		mu 0 3 77 80 76
		f 3 223 -223 -205
		mu 0 3 78 80 77
		f 3 -208 -210 -224
		mu 0 3 78 79 80;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
createNode lightLinker -s -n "lightLinker1";
	rename -uid "19736756-471D-44CB-B77E-6891FB7F64EB";
	setAttr -s 56 ".lnk";
	setAttr -s 56 ".slnk";
createNode shapeEditorManager -n "shapeEditorManager";
	rename -uid "9EAF9EF2-4554-D6B1-B874-BB89A4562C3A";
createNode poseInterpolatorManager -n "poseInterpolatorManager";
	rename -uid "305959DF-4A46-5D80-C68E-68BDAB19E54C";
createNode displayLayerManager -n "layerManager";
	rename -uid "FB1677F7-4657-9182-FB0B-72937A6D38DD";
createNode displayLayer -n "defaultLayer";
	rename -uid "1CE4DB82-4E86-F2B4-8482-E0B69A90DB8D";
createNode renderLayerManager -n "renderLayerManager";
	rename -uid "CEE068B0-42EF-E322-0A9D-0887D1E11A1C";
createNode renderLayer -n "defaultRenderLayer";
	rename -uid "9B94F0A8-43B1-B6BF-29D5-8E81D8651EC2";
	setAttr ".g" yes;
createNode phong -n "Joint_1_Object_0_Material_0";
	rename -uid "FC5151E3-44A5-63C7-262C-2BABC90F2C89";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_0_SINGLESG";
	rename -uid "9FCD2BD5-4421-FD4B-BDB3-3B82E675593F";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo1";
	rename -uid "DD1738F4-4A46-0AD4-54BE-00B6EA74C59B";
createNode file -n "Image";
	rename -uid "86E79587-46C6-C781-3F16-1090A271ADAE";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_0.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture1";
	rename -uid "DFCA4118-4051-ED26-1945-8EBA051BC4A1";
createNode phong -n "Joint_1_Object_1_Material_1";
	rename -uid "C480B0BC-4B68-8ADC-A69B-01B7C49AD5DE";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_1_SINGLESG";
	rename -uid "9A705119-4383-1342-779A-5EB7EAD1B792";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo2";
	rename -uid "8F665206-45FA-F0C0-B129-D0874B1A85EA";
createNode file -n "Image1";
	rename -uid "E7C16F89-409D-7805-DC2F-8C91D499EB96";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_1.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture2";
	rename -uid "3AB0F6D9-4481-C676-EB64-D98572513D5A";
createNode phong -n "Joint_1_Object_2_Material_2";
	rename -uid "A499E99E-49B0-F011-7B98-45ACF427B9F0";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_2_SINGLESG";
	rename -uid "8F903C03-4DE4-CCD0-FA46-26A158F0245F";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo3";
	rename -uid "0731DEAD-4297-166C-1660-6986D15DE79D";
createNode file -n "Image2";
	rename -uid "A166D384-4DF0-AAF6-50AF-D1BA6F291F93";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_2.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture3";
	rename -uid "1EF3ACA3-42FB-CD91-5543-D2BDF00A8984";
createNode phong -n "Joint_1_Object_3_Material_3";
	rename -uid "5970CC60-4D0C-A53C-335A-ED96C44C1465";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_3_SINGLESG";
	rename -uid "00EDF7CE-4093-1872-C351-CB83EE6FE26B";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo4";
	rename -uid "E2A4551A-431A-3A38-00D1-5894D1FF8A1C";
createNode file -n "Image3";
	rename -uid "CAC9DDB6-4AF2-E9D5-4D03-0780EEDB05F7";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_2.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture4";
	rename -uid "53640F91-4EF8-DD0D-70F0-5590D135B27A";
createNode phong -n "Joint_1_Object_4_Material_4";
	rename -uid "7EF00C37-41E3-5A24-0C81-4AB9339ECCAC";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_4_SINGLESG";
	rename -uid "13D7931E-4173-25CD-638C-F4BC1CC10A86";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo5";
	rename -uid "1D42A5CF-4D8B-C891-0640-73A9ECDDF0EE";
createNode file -n "Image4";
	rename -uid "D32ADB9E-4A95-EE64-3B1B-B687280D6009";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_3.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture5";
	rename -uid "5F06C14B-4127-95EB-1133-7F836DA1179D";
createNode phong -n "Joint_1_Object_5_Material_5";
	rename -uid "BE6E9F69-4A91-EE83-B917-79B4A4E12062";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_5_SINGLESG";
	rename -uid "EC979B30-4E52-1300-19ED-EAA0C1DD7FC7";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo6";
	rename -uid "0344801E-48EB-4723-2380-F3BA3DD10C68";
createNode file -n "Image5";
	rename -uid "B68E86BF-49EC-18F4-C296-B99B5D0ECF70";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_4.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture6";
	rename -uid "1B07537C-4C3F-5E86-1749-98A44DFCAB1D";
createNode phong -n "Joint_1_Object_6_Material_6";
	rename -uid "30D92A3C-463D-0092-CD67-E3B333C9DD86";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_6_SINGLESG";
	rename -uid "9B674B29-4BB6-744E-652B-3D8128869710";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo7";
	rename -uid "B510ACD1-45D1-ABCA-1669-B090E7DFEF8E";
createNode file -n "Image6";
	rename -uid "6C177843-4C33-0B0A-8FE9-DFB49BFFC0D2";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_4.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture7";
	rename -uid "602A2C56-46EF-6C64-59B4-6F8BFA343A2F";
createNode phong -n "Joint_1_Object_7_Material_7";
	rename -uid "DF3B8348-4E02-A3CD-E430-0FB9373FAF79";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_7_SINGLESG";
	rename -uid "72402101-42F1-8B38-D389-8C8984902A49";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo8";
	rename -uid "460F5A12-47F1-2CF6-ACF1-8DAF0190A7DF";
createNode file -n "Image7";
	rename -uid "E1A98CEF-40A6-78BF-98BA-E89989453765";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_5.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture8";
	rename -uid "4ED81D26-4CA4-8E49-569F-1392D319D58D";
createNode phong -n "Joint_1_Object_8_Material_8";
	rename -uid "D1ECC7AD-4C22-63A3-9C34-F48603375312";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_8_SINGLESG";
	rename -uid "A98087A3-48E3-BEBA-BD91-6C9A4E06894E";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo9";
	rename -uid "304D4880-4F16-B08A-9A1A-AF97A3A8EA9E";
createNode file -n "Image8";
	rename -uid "5E64F7DD-42E7-79C0-4D76-0BA2D7A83508";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_5.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture9";
	rename -uid "245F6709-4CD7-E08D-C303-D3A031E6900B";
createNode phong -n "Joint_1_Object_9_Material_9";
	rename -uid "1974A979-4A1E-E9BF-F7B4-87B0D29F966F";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_9_SINGLESG";
	rename -uid "78169197-4B48-E112-2A94-FEBD80195E59";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo10";
	rename -uid "13AEA19D-4523-CAC8-00F8-E7980E9470D6";
createNode file -n "Image9";
	rename -uid "5E9DDE60-4489-2C2B-25BA-949352C90E2F";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_5.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture10";
	rename -uid "0DBC2C21-490B-0332-32BA-8A8725B46924";
createNode phong -n "Joint_1_Object_10_Material_10";
	rename -uid "5DA18680-4B2D-D0F6-7940-C2A55C554FC7";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_10_SINGLESG";
	rename -uid "5FFBDE39-415E-AA22-D047-06A9BF490F24";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo11";
	rename -uid "DABCB0A3-426B-D98A-60CD-FE9A7BB28208";
createNode file -n "Image10";
	rename -uid "34368DEB-4C3A-6E85-80DC-5DABB13B8D97";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_1.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture11";
	rename -uid "6A26FEF7-48D8-2B81-2EE1-6D883D3BFBE2";
createNode phong -n "Joint_1_Object_11_Material_11";
	rename -uid "9854A1E3-4CDB-2583-BA99-AFB0BA6F491C";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_11_SINGLESG";
	rename -uid "7C5BC91E-41FA-629E-15DC-D681C5FBF541";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo12";
	rename -uid "D0393232-49AA-E4DB-D90F-788151433214";
createNode file -n "Image11";
	rename -uid "FDA56923-4AB8-23B3-B245-87B4A44BF3C4";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_6.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture12";
	rename -uid "07BE7CCA-42D5-CBAA-F99F-5D832923C026";
createNode phong -n "Joint_1_Object_12_Material_12";
	rename -uid "0098C7E2-4B65-53F3-7E3A-768C9D44BA59";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_12_SINGLESG";
	rename -uid "73108CF7-4FF1-0CFC-4683-3D98F23AFEB7";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo13";
	rename -uid "45AD627B-4D70-B652-1761-A9A60F4F9A74";
createNode file -n "Image12";
	rename -uid "86E77FA9-4499-104D-4A86-2B9D4BE4AB3A";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_7.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture13";
	rename -uid "5B24DE0D-4BA0-FB88-3D2E-069E1830299A";
createNode phong -n "Joint_1_Object_13_Material_13";
	rename -uid "3F0B3A61-4A28-1300-1FA0-C5A26943326D";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_13_SINGLESG";
	rename -uid "BC9E93CA-4676-2B32-7D22-049573D01548";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo14";
	rename -uid "E5C3BCC6-485B-115D-BADB-4EA7F1C02D8D";
createNode file -n "Image13";
	rename -uid "DD5BD2C0-430D-A4BA-EBD7-B98536B115EA";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_8.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture14";
	rename -uid "2CD75A8D-4510-F2EE-18DE-788DD34C29D9";
createNode phong -n "Joint_1_Object_14_Material_14";
	rename -uid "20823413-4056-96B7-B4D2-499B344AD0B8";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_14_SINGLESG";
	rename -uid "C6C21D5C-4F13-9FD9-1A73-C4BBA5E53A7C";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo15";
	rename -uid "35894A73-41EA-F9C2-446C-20BCA33C3E3B";
createNode file -n "Image14";
	rename -uid "622EC93F-441B-BBE2-87E2-038FF39EE9B6";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_9.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture15";
	rename -uid "B6628397-4867-F57F-EF92-FCB70F6C9505";
createNode phong -n "Joint_1_Object_15_Material_15";
	rename -uid "800D391E-4489-CE98-E422-F89370E5AE50";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_15_SINGLESG";
	rename -uid "FB47942B-4C5C-3307-A231-4E8C44E4F246";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo16";
	rename -uid "7423BD94-4301-E023-07CE-B99BFAAF924F";
createNode file -n "Image15";
	rename -uid "302CA3B3-4F29-7E4E-BDF8-77B37BE10F83";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_10.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture16";
	rename -uid "128B691E-4F45-349E-A846-B49516895347";
createNode phong -n "Joint_1_Object_16_Material_16";
	rename -uid "F542D111-41E7-4F6E-252A-C2A36A4F18AE";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_16_SINGLESG";
	rename -uid "4C2877D9-4061-8E84-04AC-10B266B4FA43";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo17";
	rename -uid "A246F7BA-4342-BFA6-724A-4D835FBA7545";
createNode file -n "Image16";
	rename -uid "CF461797-410E-BE16-BACF-B892C1AA3549";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_11.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture17";
	rename -uid "30F488DB-4EAC-7F20-0E07-58A3AD08F9D6";
createNode phong -n "Joint_1_Object_17_Material_17";
	rename -uid "1B765531-4269-75E6-F6BB-2A8C06FBAC3D";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_17_SINGLESG";
	rename -uid "70C4B670-4FA9-AFDF-5ABE-CD94B3309E3A";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo18";
	rename -uid "8F57EF8E-4C65-DB5E-F356-8AB0553B728D";
createNode file -n "Image17";
	rename -uid "DCF5BBB8-4ADB-1CE6-E2A4-D78E7A617353";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_12.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture18";
	rename -uid "59FC6905-47EE-FA45-4E36-789DE5E92EC9";
createNode phong -n "Joint_1_Object_18_Material_18";
	rename -uid "46F770E0-453B-1967-40A5-3CA536D5747F";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_18_SINGLESG";
	rename -uid "BD902D50-4648-CDCC-968F-4D95C3F65D8B";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo19";
	rename -uid "6A510B77-481A-90C7-5942-789364D9322E";
createNode file -n "Image18";
	rename -uid "81A1978B-4D80-E1FE-518A-DD9A537079ED";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_13.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture19";
	rename -uid "98BAC278-4D20-F8EA-4852-238CE6F0DA54";
createNode phong -n "Joint_1_Object_19_Material_19";
	rename -uid "AB8F5D3E-4C2E-E28E-822D-229FBE2B476E";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_19_SINGLESG";
	rename -uid "90A78DDD-40F4-5986-9FA7-E5BA2C243E63";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo20";
	rename -uid "D99E4C27-416E-C4FE-5B40-EE86208A8028";
createNode file -n "Image19";
	rename -uid "9F9C6F2C-4ECF-9A31-866D-059B0A296A1D";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_14.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture20";
	rename -uid "E22E7A73-43E9-835C-9B3A-FD86002C9B7E";
createNode phong -n "Joint_1_Object_20_Material_20";
	rename -uid "7C43FBA8-43F2-5E9C-4728-E19013F64E5A";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_20_SINGLESG";
	rename -uid "FEFA4DEC-4C42-8DBF-A996-6EB94D33FEB0";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo21";
	rename -uid "463D7C66-4B0A-BD7A-23C5-AB8653699356";
createNode file -n "Image20";
	rename -uid "9A1227D8-4886-1B48-1F92-5DBF469CF0BC";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_14.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture21";
	rename -uid "F96E9F0B-4CDA-2E58-FB77-1A8F9A367749";
createNode phong -n "Joint_1_Object_21_Material_21";
	rename -uid "7A0576F0-49D7-83EF-8FB4-A3A4B0DE664B";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_21_SINGLESG";
	rename -uid "32446855-45A3-37A7-A177-E482DB1A26E8";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo22";
	rename -uid "54BD89BF-46C6-0068-67BE-2E8A29106A1F";
createNode file -n "Image21";
	rename -uid "E5372220-4F70-FCA6-D1B1-E280747E1C8D";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_15.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture22";
	rename -uid "4AAF9D1A-4885-0582-FD47-69AC9EA51BCA";
createNode phong -n "Joint_1_Object_22_Material_22";
	rename -uid "1F0F2289-4C8B-5EE2-206B-768ECA34A1ED";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_22_SINGLESG";
	rename -uid "341FDF14-4265-2E64-19CA-ABBA018EDF97";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo23";
	rename -uid "C3043235-4B76-6921-A075-6D81463440D6";
createNode file -n "Image22";
	rename -uid "9FA392CE-477D-22A8-18DE-28B6125F03FA";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_16.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture23";
	rename -uid "75F920AB-499B-4BC6-119A-D9889B032BBE";
createNode phong -n "Joint_1_Object_23_Material_23";
	rename -uid "395A5C9C-43EF-8173-A725-FD99230A8135";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_23_SINGLESG";
	rename -uid "3667821D-4DF0-42D1-C32E-EFA8EFE45EAB";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo24";
	rename -uid "24B90955-4DD7-F52C-C054-7BBAB8C93596";
createNode file -n "Image23";
	rename -uid "F1B9C2BC-4207-BE91-6E36-2695BD7FCC2F";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_17.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture24";
	rename -uid "CB6FCC92-4E24-9F3D-D0FB-62B46810D797";
createNode phong -n "Joint_1_Object_24_Material_24";
	rename -uid "F4B99FC2-4A50-029A-8067-B692AAA271B0";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_24_SINGLESG";
	rename -uid "E2BF366C-46BF-1013-5B81-2BA04E70AAF5";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo25";
	rename -uid "723DF422-49F3-EE48-2C4C-C3B8D058BCE7";
createNode file -n "Image24";
	rename -uid "9CEE0D90-4311-BBD1-4D5D-9094D55B187A";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_18.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture25";
	rename -uid "C22F5E0E-4496-515F-CFA2-21969B8BF072";
createNode phong -n "Joint_1_Object_25_Material_25";
	rename -uid "3DBEDED4-4FEA-3086-AF7A-8293E120A19B";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_25_SINGLESG";
	rename -uid "FE0D196E-4AEE-4D3A-3C7B-B08719E18E41";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo26";
	rename -uid "01B7FC24-4341-21B2-4EE5-C9A3D5437C99";
createNode file -n "Image25";
	rename -uid "E9728164-4326-0672-C6DD-DEB27692330D";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_19.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture26";
	rename -uid "BD7B9244-40F3-2D82-4717-E5AFFFA5CC75";
createNode phong -n "Joint_1_Object_26_Material_26";
	rename -uid "DAAA46D0-4840-AA6F-8699-2BB52CFC2092";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_26_SINGLESG";
	rename -uid "D6EC6133-4BBB-5DF3-ADBA-85A6CCCA1A25";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo27";
	rename -uid "AC1E6995-4FF7-5ACE-8753-18BB7E134020";
createNode file -n "Image26";
	rename -uid "92509E8B-48BF-1A1C-4AE1-E78CDA4C779C";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Joint_1_Object_26_Material_26";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture27";
	rename -uid "16B28B06-4654-6461-06C3-16858A5E8EEA";
createNode phong -n "Joint_1_Object_27_Material_27";
	rename -uid "A20ABB30-424C-3464-B7ED-51B9990F9C9A";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_27_SINGLESG";
	rename -uid "BF29BD09-4A27-C0DA-356B-DB96D58934FE";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo28";
	rename -uid "54C40405-4B53-A135-7D0C-CB8315A18FEC";
createNode file -n "Image27";
	rename -uid "1D84F278-468F-DEA3-4B90-6D8931352A30";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_8.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture28";
	rename -uid "E68A2FDD-462B-6E45-1BD6-B5A0CE9DADA6";
createNode phong -n "Joint_1_Object_28_Material_28";
	rename -uid "6E96927F-40FB-78FA-3BCB-A2A64A07AB3A";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_28_SINGLESG";
	rename -uid "75D4718D-48DB-85AE-9FAF-9EB9DF284AE4";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo29";
	rename -uid "AB427722-4B21-20DD-1339-3A9C16355562";
createNode file -n "Image28";
	rename -uid "2B45C88A-4343-7AE5-98E3-3AA820F7EFD2";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_7.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture29";
	rename -uid "C1E2EBDB-4097-A9C7-E550-1696949C6ACC";
createNode phong -n "Joint_1_Object_29_Material_29";
	rename -uid "CFFB5BA4-4B8C-C038-B1B9-3EB1A32F0514";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_29_SINGLESG";
	rename -uid "98DAB485-44A6-55A8-49F9-1ABCD4613D82";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo30";
	rename -uid "44F1B99E-4FEC-4527-619C-3AB93D62CE04";
createNode file -n "Image29";
	rename -uid "D5AF8B95-43A8-3D59-5696-D3894A64C9BC";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_9.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture30";
	rename -uid "1E78E61F-484D-8CB2-ED61-EF888214A026";
createNode phong -n "Joint_1_Object_30_Material_30";
	rename -uid "73EA2931-423A-261E-E40E-B8901058D1B0";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_30_SINGLESG";
	rename -uid "74F8F058-40D4-81CB-09E8-6AB52A1B1C3C";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo31";
	rename -uid "F393143D-4D01-F98E-F0C1-9094C4980FCE";
createNode file -n "Image30";
	rename -uid "BE7AC18B-4EBC-818D-6566-F9B1454CEABC";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_20.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture31";
	rename -uid "5415A1DC-4CE4-BAA4-6A5E-9A9956B3C5A4";
createNode phong -n "Joint_1_Object_31_Material_31";
	rename -uid "8DCDFBFF-468E-781C-9C1B-64B6C13E623E";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_31_SINGLESG";
	rename -uid "58DBF705-4593-8F3D-EA3D-D4B30271B9FC";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo32";
	rename -uid "8BB23B7C-45F7-9053-CFDE-A288A22721DE";
createNode file -n "Image31";
	rename -uid "4657D706-448D-0BF6-D17A-2E97ECF39793";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_13.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture32";
	rename -uid "62522655-479E-DEBF-218C-7C838F41FEB0";
createNode phong -n "Joint_1_Object_32_Material_32";
	rename -uid "D96521F4-406F-21FE-AD48-7295DDF0D936";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_32_SINGLESG";
	rename -uid "A20225CE-4AC1-7E97-9677-B5939F190D01";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo33";
	rename -uid "B6B4A425-4BAE-F279-0531-EABEE0CFA0E1";
createNode file -n "Image32";
	rename -uid "4BE52373-4A42-53D3-67A8-F090BDE2C5B4";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_14.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture33";
	rename -uid "A35C84A6-4B7C-7CDA-C864-4D80206D2B7A";
createNode phong -n "Joint_1_Object_33_Material_33";
	rename -uid "59A8085F-461B-7C09-D007-B9A474D850DC";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_33_SINGLESG";
	rename -uid "24EB0D21-4BE3-41F9-B7AC-BFAE0AE3B93C";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo34";
	rename -uid "41DEA7E0-4D8F-F056-D0A5-9C9C3DF26CE2";
createNode file -n "Image33";
	rename -uid "7600BE6A-4EBB-D3E4-99DD-8C92C07C215E";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_18.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture34";
	rename -uid "8BAACFA4-4828-F237-0D49-F1950C7ACFD5";
createNode phong -n "Joint_1_Object_34_Material_34";
	rename -uid "E614EF57-4C7F-3072-6001-B99B5CAF11EF";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_34_SINGLESG";
	rename -uid "C3FDEA4E-4407-E284-A4F4-C0829688A4DC";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo35";
	rename -uid "108AAB67-494D-97C7-C535-98BCD0674D89";
createNode file -n "Image34";
	rename -uid "E1FFB6CF-42B9-B05F-11E4-FC89A2389B3A";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_20.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture35";
	rename -uid "DE014974-4931-04BB-9A53-8A8268D5F490";
createNode phong -n "Joint_1_Object_35_Material_35";
	rename -uid "4E125911-49E8-6078-0EF8-3886CDC847D5";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_35_SINGLESG";
	rename -uid "58E2CDE1-436D-0945-44BE-28AABC8BC334";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo36";
	rename -uid "87415513-4A47-9501-AB21-04A1FFE50129";
createNode file -n "Image35";
	rename -uid "099C8926-4740-A458-D15F-1B9CADC9C836";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_15.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture36";
	rename -uid "F4631CC3-44E5-F3B2-18BF-EA92639B3D91";
createNode phong -n "Joint_1_Object_36_Material_36";
	rename -uid "327D9244-4243-5215-2F3E-14A4015C3EE5";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_36_SINGLESG";
	rename -uid "41731A5E-4828-F699-24AC-FE985D1A327D";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo37";
	rename -uid "DD4FF7EF-44EB-BA4B-B469-77880283E250";
createNode file -n "Image36";
	rename -uid "58A5F77E-4FEE-CEB1-C02F-76B126CEC56E";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_16.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture37";
	rename -uid "513FD17D-48AA-ECC3-1843-ED992B92C0E7";
createNode phong -n "Joint_1_Object_37_Material_37";
	rename -uid "255CDE2F-4921-AF3C-530C-CFAED5E74C3A";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_37_SINGLESG";
	rename -uid "05E145B8-4BBD-199B-D0B0-67B2C6597630";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo38";
	rename -uid "FC8889FC-45D2-BFAC-20B2-4192AA45B3E0";
createNode file -n "Image37";
	rename -uid "B71F60A2-4B39-76DC-9CD5-0CA2E72548EA";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_17.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture38";
	rename -uid "E13133AE-42D8-7058-2266-25A65DB4ED98";
createNode phong -n "Joint_1_Object_38_Material_38";
	rename -uid "763E0FED-4955-5C2E-7486-3AAF8AB9C547";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_38_SINGLESG";
	rename -uid "0C1355D0-4B68-B709-E304-B6B5EB9B3296";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo39";
	rename -uid "47B66BFA-4729-741B-4125-D2928809ABEC";
createNode file -n "Image38";
	rename -uid "3A50E054-496E-5C19-463F-8995A934E1AC";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_21.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture39";
	rename -uid "38352D7F-4333-5C79-1630-11AC4F3169A8";
createNode phong -n "Joint_1_Object_39_Material_39";
	rename -uid "21B24EDE-4979-9398-9157-9C8E903C2334";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_39_SINGLESG";
	rename -uid "3EAF0849-403A-B51E-9A26-C98E8A21C58F";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo40";
	rename -uid "6AEAEA75-40EE-6CE4-ACEF-8C9FEB719F78";
createNode file -n "Image39";
	rename -uid "BC27BC22-46E8-38B8-347C-B28C12D4286B";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_1.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture40";
	rename -uid "406C4D04-42FA-E6B5-557A-18938560DDBD";
createNode phong -n "Joint_1_Object_40_Material_40";
	rename -uid "B8DFD40D-4FB5-B25A-6D1E-C38BF5605F85";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_40_SINGLESG";
	rename -uid "81FEFC12-4AF2-D233-C427-12A44BF620B3";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo41";
	rename -uid "748F6309-49A0-AB82-F1E3-25A55B7B4D10";
createNode file -n "Image40";
	rename -uid "22D5E165-4D76-2663-C597-199C4823A9F4";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_22.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture41";
	rename -uid "18644B40-4ABD-45A5-442E-ABA331AA5556";
createNode phong -n "Joint_1_Object_41_Material_41";
	rename -uid "7F167D80-43EC-87BF-2F79-3BB81FE519B0";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_41_SINGLESG";
	rename -uid "C8111BA7-4123-179E-FBE2-A1B9C9EDF43F";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo42";
	rename -uid "4CCE3D27-4452-83C8-40BC-8A935AE65511";
createNode file -n "Image41";
	rename -uid "1437C423-49FF-7D64-4A80-59929027A157";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_21.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture42";
	rename -uid "8ABA3C72-4AB2-35E6-2AB2-4BB51F365A32";
createNode phong -n "Joint_1_Object_42_Material_42";
	rename -uid "C6563A7B-4B96-60FE-AF20-238E9C25A6CC";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_42_SINGLESG";
	rename -uid "6A066480-48A9-FAA7-08DA-37BF96C17EF9";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo43";
	rename -uid "8F623000-455D-2964-135F-5CB095E23CE4";
createNode file -n "Image42";
	rename -uid "9F992E0C-431D-9B9E-DA1B-77A77D0B83E9";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_1.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture43";
	rename -uid "6D931A81-4E9B-211C-F192-A2A4275DEA4E";
createNode phong -n "Joint_1_Object_43_Material_43";
	rename -uid "9BB03D9B-4725-C5E7-67FC-6D89F3E84C31";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_43_SINGLESG";
	rename -uid "1BDDA28E-4A31-A76C-ADB7-1899B03F5C61";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo44";
	rename -uid "90DC3CCA-4F39-5C5B-95BE-F3B58C317AAA";
createNode file -n "Image43";
	rename -uid "4A0C83FE-4CFC-33B4-600C-4A9383732A93";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_22.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture44";
	rename -uid "A58807D8-40B3-28EF-E453-E6B194065932";
createNode phong -n "Joint_1_Object_44_Material_44";
	rename -uid "F7C09312-4F4A-A084-B503-BFB2690CFB80";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_44_SINGLESG";
	rename -uid "D130F9FF-483A-87F0-C94E-B18B68E78084";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo45";
	rename -uid "6B58991B-43E7-7057-45C9-92BA96C649EF";
createNode file -n "Image44";
	rename -uid "BE6C8830-410B-03F7-E0C6-C384D47D6FF7";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_21.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture45";
	rename -uid "43B59BE6-4BDF-2099-828D-2EBFCBE2157B";
createNode phong -n "Joint_1_Object_45_Material_45";
	rename -uid "0B521C49-4F34-5DB9-1439-E39F8735A45B";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_45_SINGLESG";
	rename -uid "F91CE720-4F3D-84B8-D23C-5BAFAE87E022";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo46";
	rename -uid "F8DA0E53-43CA-7EB7-B4B3-C79F82D953D2";
createNode file -n "Image45";
	rename -uid "654328E5-4EF1-34B7-48B5-9086BA461154";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_1.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture46";
	rename -uid "68BE5201-4B8B-C2E6-75CB-60BED145B23B";
createNode phong -n "Joint_1_Object_46_Material_46";
	rename -uid "FCBB0F48-4DC9-6E97-DD01-A5868DF3E777";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_46_SINGLESG";
	rename -uid "9261320F-4FC5-9D01-A020-A4B2D2F6959E";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo47";
	rename -uid "42ACE42F-4DFE-BFAF-FCDD-FB93D3CF470C";
createNode file -n "Image46";
	rename -uid "D2E67F10-4427-104B-7142-72A1E1426587";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_22.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture47";
	rename -uid "6AAE09F3-4A60-AE00-EB61-9B961E300AC0";
createNode phong -n "Joint_1_Object_47_Material_47";
	rename -uid "5B210F4F-4EC0-F92B-D1C8-F0A85A797FAC";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_47_SINGLESG";
	rename -uid "1585DC17-4AF5-E1E4-2C7E-7D930DFCFA02";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo48";
	rename -uid "300A81C2-4B9D-7870-E17D-7DA56BDEC06A";
createNode file -n "Image47";
	rename -uid "3F4930D7-474A-FF24-2E72-0AA9075688A9";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_21.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture48";
	rename -uid "9A9A16E2-47DA-8491-86C6-F2BEE30D0087";
createNode phong -n "Joint_1_Object_48_Material_48";
	rename -uid "1D93668F-42C7-4899-8398-F6A2CBFB39D1";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_48_SINGLESG";
	rename -uid "25F18282-4121-0F2F-92DF-72925A3BEAF1";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo49";
	rename -uid "31CE0C5F-41A9-0BF3-7E68-A899834E8E9F";
createNode file -n "Image48";
	rename -uid "209C5F18-4D9E-FD2E-F623-0F8BA20BBB5B";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_1.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture49";
	rename -uid "4B8AB10A-4085-EEF9-A6F2-10AC283C8AD3";
createNode phong -n "Joint_1_Object_49_Material_49";
	rename -uid "130B7A4D-4DFF-B39F-54CE-EDB1B35F4648";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_49_SINGLESG";
	rename -uid "14D17F0C-412A-C9FF-E76A-7FA27B6194EB";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo50";
	rename -uid "91B02C92-4235-93FB-813B-AA9A91338496";
createNode file -n "Image49";
	rename -uid "4A0D5BE1-4C79-2537-E68A-AFA111B8496A";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_22.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture50";
	rename -uid "FBCF654A-4F12-0D96-1B39-028D87ED6C7C";
createNode phong -n "Joint_1_Object_50_Material_50";
	rename -uid "60D86DDA-43BF-F66A-0883-8B899BC27960";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_50_SINGLESG";
	rename -uid "03AD2978-47FE-FDDC-D17B-BCA966B028A4";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo51";
	rename -uid "6DFF03AC-46F0-C18E-3131-5CBC928BED32";
createNode file -n "Image50";
	rename -uid "6EAD4B89-4EDE-F213-7E5E-EF840A05F793";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_23.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture51";
	rename -uid "B0765EAC-4433-1CC5-C6EB-5782EA5AB054";
createNode phong -n "Joint_1_Object_51_Material_51";
	rename -uid "D4CBB9AB-4117-C6FF-A5D2-669F6742E46F";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_51_SINGLESG";
	rename -uid "AE8CD724-40B7-3C30-19CF-858C8050E587";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo52";
	rename -uid "BC815F5C-420F-992F-D69E-B788A167B39D";
createNode file -n "Image51";
	rename -uid "A043174A-402D-9035-B7EA-799026172E73";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_23.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture52";
	rename -uid "3A9116F6-47F8-B518-FC4C-F5A66FA1A094";
createNode phong -n "Joint_1_Object_52_Material_52";
	rename -uid "55DF0D33-4D9F-6B2F-E55E-2B8DF8BA06F7";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_52_SINGLESG";
	rename -uid "548706C5-48B1-ADDE-DB7B-0DA4DC4FC5AE";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo53";
	rename -uid "29A80BD3-4E8D-24EB-EAB6-01A375F2982C";
createNode file -n "Image52";
	rename -uid "B30885C4-4E7E-71AE-4B7E-D783F2A0F709";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_23.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture53";
	rename -uid "73FF6532-47C6-8A99-E162-70BE002976F4";
createNode phong -n "Joint_1_Object_53_Material_53";
	rename -uid "11CA4254-4412-D668-2BAB-C29CAECFFF49";
	setAttr ".dc" 1;
	setAttr ".sc" -type "float3" 1 1 1 ;
	setAttr ".rfl" 1;
	setAttr ".cp" 2;
createNode shadingEngine -n "Joint_1_Object_53_SINGLESG";
	rename -uid "D2FC81A6-4296-5209-2E97-D68D502B626E";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo54";
	rename -uid "ED38B090-40D0-9985-9A0A-3CB85E7B7484";
createNode file -n "Image53";
	rename -uid "381CB758-458B-5548-A44B-BAAFA09FC431";
	setAttr ".ftn" -type "string" "C:\\Users\\Caleb Robinson\\Desktop\\Multimedia\\Noesis\\noesisv44191\\Texture_23.png";
	setAttr ".cs" -type "string" "sRGB";
createNode place2dTexture -n "place2dTexture54";
	rename -uid "3DF2ED39-43FA-8613-88AE-C7AAD4428D4E";
createNode skinCluster -n "skinCluster1";
	rename -uid "57A869D4-48AE-23BD-691B-9CAC72D90503";
	setAttr ".skm" -1;
	setAttr -s 15 ".wl";
	setAttr ".wl[0:14].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak1";
	rename -uid "07275E73-453D-F936-05FD-10BA5E4F4C1D";
createNode objectSet -n "skinCluster1Set";
	rename -uid "5A4C9481-4461-777B-39C7-628FC8B7205B";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster1GroupId";
	rename -uid "C6B18491-4D0C-4247-44AE-948C00C88B38";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster1GroupParts";
	rename -uid "AEE58D2C-4B12-9774-D0CA-1D984B2B846B";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:14]";
createNode objectSet -n "tweakSet1";
	rename -uid "19631FD5-4DD5-3160-75E9-A4ABA1E9196E";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId2";
	rename -uid "A3C7DEC3-4923-692F-E298-5FB790BE7720";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts2";
	rename -uid "C3F4FEDA-41DC-3378-0210-A19B7170C8B4";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode dagPose -n "bindPose1";
	rename -uid "DEB9960B-446C-1C2E-D7F1-DA9C0B8FFB93";
	setAttr -s 2 ".wm";
	setAttr -s 2 ".xm";
	setAttr ".xm[0]" -type "matrix" "xform" 1 1 1 0 -0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 no;
	setAttr ".xm[1]" -type "matrix" "xform" 0.99999979937318417 0.99999975603761693 0.99999993567465617 0.41748109705563852
		 -0.56652773250840649 -0.74465326038405544 0 2.6291908075426713 7.3291579413985923
		 -3.8642372965248222 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 no;
	setAttr -s 2 ".m";
	setAttr -s 2 ".p";
	setAttr ".bp" yes;
createNode skinCluster -n "skinCluster2";
	rename -uid "D1DCD896-4ED0-E75E-A632-BEA8E2195CBE";
	setAttr ".skm" -1;
	setAttr -s 38 ".wl";
	setAttr ".wl[0:37].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak2";
	rename -uid "8F8936DE-42E5-F574-4124-039F4FA14EBB";
createNode objectSet -n "skinCluster2Set";
	rename -uid "7D58158C-4C1C-54E2-CB4D-BAB87A4C9AD0";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster2GroupId";
	rename -uid "EA86ABAF-411F-0872-0E9B-B9A76701988B";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster2GroupParts";
	rename -uid "5089C14F-4331-9D6C-BD52-92A978286F51";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:37]";
createNode objectSet -n "tweakSet2";
	rename -uid "BE6C1BE9-4254-9B61-80A9-6C98D3F543C4";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId4";
	rename -uid "D4C0FA97-48C4-FD81-5246-49824E9F570B";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts4";
	rename -uid "2BBEE235-4C90-A204-3BE3-149C693D7129";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster3";
	rename -uid "D644EC60-4822-D053-1EFD-D48C4CCF85BF";
	setAttr ".skm" -1;
	setAttr -s 30 ".wl";
	setAttr ".wl[0:29].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak3";
	rename -uid "FA70CC59-4D80-0911-3BB3-D1A7413B1C44";
createNode objectSet -n "skinCluster3Set";
	rename -uid "2BCBFB0B-44CB-CC7C-A37D-2D8F794E59C6";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster3GroupId";
	rename -uid "9907A333-4810-943D-4B3F-6FA59CEF9BD3";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster3GroupParts";
	rename -uid "1405FE2B-438C-91F0-750B-CAA283B106A0";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:29]";
createNode objectSet -n "tweakSet3";
	rename -uid "2B1AD3E0-4456-6F13-9785-5EA2600ACBB3";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId6";
	rename -uid "DACA3FE8-49C4-109E-CBC9-508776CE371A";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts6";
	rename -uid "188BB055-49F2-F898-EBF0-5AB62DC233BF";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster4";
	rename -uid "A06044C8-4261-9803-6BC7-DE9061BFF295";
	setAttr ".skm" -1;
	setAttr -s 6 ".wl";
	setAttr ".wl[0:5].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak4";
	rename -uid "5B427F7C-4897-14B3-EC7C-A98F5C1DAA6C";
createNode objectSet -n "skinCluster4Set";
	rename -uid "C8CDE19F-4283-D271-9371-2B927838BB70";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster4GroupId";
	rename -uid "EBE2F514-40EF-3915-7066-418753981F4B";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster4GroupParts";
	rename -uid "7E476E9B-4650-E762-0B9E-B0874F296985";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:5]";
createNode objectSet -n "tweakSet4";
	rename -uid "3EC4039A-404E-DF38-B519-8CA56BC02C95";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId8";
	rename -uid "93FF7705-4B9C-CFB0-8F99-D69135D34BB1";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts8";
	rename -uid "C21B94F5-4D50-A379-80E5-81B9F0AF73E1";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster5";
	rename -uid "EA8329B5-4F07-A9B5-BB48-018EFFF3EC93";
	setAttr ".skm" -1;
	setAttr -s 13 ".wl";
	setAttr ".wl[0:12].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak5";
	rename -uid "D8E64AA7-4D06-ABD3-B229-50879AF99F2F";
createNode objectSet -n "skinCluster5Set";
	rename -uid "6CAAC6E9-42AB-753B-A7EC-B2A96630DB95";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster5GroupId";
	rename -uid "49143C9A-4C1C-77D7-9419-599CBAA6FE26";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster5GroupParts";
	rename -uid "D8D399BF-49D3-01C3-26C3-0D8469F246B6";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:12]";
createNode objectSet -n "tweakSet5";
	rename -uid "619C34BF-412B-EFBE-E433-0D8F3F231BCA";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId10";
	rename -uid "8F542A1B-4E9F-B02D-DB14-5791D0F24732";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts10";
	rename -uid "581A2331-4B25-1016-0432-92B0FD344A4F";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster6";
	rename -uid "D9A2EAF9-441A-F1BB-D388-4CB402E4DD71";
	setAttr ".skm" -1;
	setAttr -s 4 ".wl";
	setAttr ".wl[0:3].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak6";
	rename -uid "C68A1094-4320-AB89-1733-B2B3AB4A6DB3";
createNode objectSet -n "skinCluster6Set";
	rename -uid "7D359AF5-49E3-2174-EDA0-3480672EC6CC";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster6GroupId";
	rename -uid "6947DF34-419F-AE84-3297-AABE1C3BFFD9";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster6GroupParts";
	rename -uid "8CFCC682-48D9-40CA-0805-0C81399DC09C";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:3]";
createNode objectSet -n "tweakSet6";
	rename -uid "A38F42DE-4EA4-A254-7B8F-93A68E42261C";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId12";
	rename -uid "A0E58065-4C9D-1711-E770-4AA749BCA748";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts12";
	rename -uid "142C5E67-42CB-EC95-D211-DABFC4B960FA";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster7";
	rename -uid "6E4234B5-4114-401F-CDF0-CA9E86D1011C";
	setAttr ".skm" -1;
	setAttr -s 26 ".wl";
	setAttr ".wl[0:25].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak7";
	rename -uid "36DD4FC7-41AC-D177-DE79-CCB09EE5614B";
createNode objectSet -n "skinCluster7Set";
	rename -uid "21565405-4CCD-402D-C4B7-F9A38D94DA40";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster7GroupId";
	rename -uid "54B7BC14-4F75-CD57-B6D9-B9BEBB936C7E";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster7GroupParts";
	rename -uid "F4267C6B-45DB-3CD2-5240-FDAF0A9E9EF2";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:25]";
createNode objectSet -n "tweakSet7";
	rename -uid "FB72D760-44AB-DDFD-4DD8-088F9BF1CCCB";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId14";
	rename -uid "A154F952-4A3A-CB31-7DA7-CF85010458CA";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts14";
	rename -uid "7BD911F5-4156-C7A7-4355-69B980CD0B63";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster8";
	rename -uid "976C4CAE-4E6D-2B1E-C386-E0ACDB893B52";
	setAttr ".skm" -1;
	setAttr -s 32 ".wl";
	setAttr ".wl[0:31].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak8";
	rename -uid "6A0AFBD5-4A01-4A00-9CB0-1096CD5A40FE";
createNode objectSet -n "skinCluster8Set";
	rename -uid "B0295B62-4671-102F-70DC-AB8CE854272D";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster8GroupId";
	rename -uid "68FCA226-4D93-3216-9109-A2B9638451C5";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster8GroupParts";
	rename -uid "08A1A220-41DC-318E-F04F-FDA5965007E2";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:31]";
createNode objectSet -n "tweakSet8";
	rename -uid "F21F6438-4A1E-8A1B-9FAC-AB9D36486CD0";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId16";
	rename -uid "3A7C682F-4156-D9A8-4BF6-188BBEE38530";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts16";
	rename -uid "212DCCF8-43AC-A808-733E-EE93321CF110";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster9";
	rename -uid "BFE6357C-448C-5953-5EE2-72836CCAD654";
	setAttr ".skm" -1;
	setAttr -s 27 ".wl";
	setAttr ".wl[0:26].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak9";
	rename -uid "5A199946-4CFC-C77D-695F-949924A04F40";
createNode objectSet -n "skinCluster9Set";
	rename -uid "16EA8A56-4DF8-3E08-1959-948B8A6CADC9";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster9GroupId";
	rename -uid "AC3790CE-4BA5-6D1C-5759-50ACD684F4ED";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster9GroupParts";
	rename -uid "108B09FF-4A6E-DBCE-96B9-B2B727FA06A9";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:26]";
createNode objectSet -n "tweakSet9";
	rename -uid "EC05FFBD-4515-8548-E3F5-7C9F6E545E1A";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId18";
	rename -uid "BCC843D3-48C4-E5CF-2C8C-4FA1E4A36879";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts18";
	rename -uid "5C46716F-41F1-9D00-1EB8-6A9DD97A0D6B";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster10";
	rename -uid "8D761DA2-44FC-F672-C0EB-D8AD180EB98B";
	setAttr ".skm" -1;
	setAttr -s 26 ".wl";
	setAttr ".wl[0:25].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak10";
	rename -uid "099365B6-4F8F-3762-653D-5FB41FE94800";
createNode objectSet -n "skinCluster10Set";
	rename -uid "FAF208B0-4139-DFBB-CB37-71BD7AC3C1C0";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster10GroupId";
	rename -uid "F19F3E7B-453B-33A8-F460-67A8CF5B0CCD";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster10GroupParts";
	rename -uid "FE196056-4D7B-79D7-4CD2-D9A483F000B8";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:25]";
createNode objectSet -n "tweakSet10";
	rename -uid "8E66254E-4EC2-C6F4-41F0-C0A00A796CB2";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId20";
	rename -uid "3DF1EA23-4E60-C57F-71B2-EA8A84D2B5F9";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts20";
	rename -uid "EADBB77B-4004-ABC5-9463-4996756395FA";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster11";
	rename -uid "82950B2E-40C1-7AED-F8EE-DA9B13E7A45D";
	setAttr ".skm" -1;
	setAttr -s 54 ".wl";
	setAttr ".wl[0:53].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak11";
	rename -uid "7D5012D4-48E9-1C07-9111-D6B82D95C97E";
createNode objectSet -n "skinCluster11Set";
	rename -uid "32DAC42F-480D-8336-578C-9D85B8B381D5";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster11GroupId";
	rename -uid "EE3C4B23-4B8C-AA5B-73CF-F0879F14CD06";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster11GroupParts";
	rename -uid "4A197A48-46CA-A3D7-4211-29B2118FC045";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:53]";
createNode objectSet -n "tweakSet11";
	rename -uid "341A55D6-4CD8-BA71-4DFA-D8A77DA382D2";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId22";
	rename -uid "B962CDCC-4B59-C96E-7DC4-EBA5D469EAF9";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts22";
	rename -uid "1EEFA8B0-4867-A739-996D-AEAEE740FC86";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster12";
	rename -uid "44DF4AF6-45E3-EDFF-1E3D-A3A5365FBE5B";
	setAttr ".skm" -1;
	setAttr -s 3 ".wl";
	setAttr ".wl[0:2].w"
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak12";
	rename -uid "3DE0F9CB-42A5-F0A5-E8FB-47BCD3FF5FAA";
createNode objectSet -n "skinCluster12Set";
	rename -uid "765FB606-48D7-BDD1-FC57-67BBA089BEFE";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster12GroupId";
	rename -uid "AD8D990C-4850-9620-726E-DFA89365CBC3";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster12GroupParts";
	rename -uid "AB7536B3-4E90-56D7-3171-03BA6977EA4F";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:2]";
createNode objectSet -n "tweakSet12";
	rename -uid "9D8E4E44-4363-615E-F156-DEAC830D34D1";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId24";
	rename -uid "6A877E42-4F56-A002-F719-1D8F711EDAB3";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts24";
	rename -uid "27F96B3C-4D19-AEBC-7326-70A5DEC5778A";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster13";
	rename -uid "90F1BFB4-4BE8-75F1-373A-74B76D7AEB09";
	setAttr ".skm" -1;
	setAttr -s 4 ".wl";
	setAttr ".wl[0:3].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak13";
	rename -uid "B0E259A4-4B4D-89CB-45D8-F9823A5DB0D0";
createNode objectSet -n "skinCluster13Set";
	rename -uid "6275E645-4D91-F9B1-85B5-3EBEA83CB9F9";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster13GroupId";
	rename -uid "24E4A683-456F-F4B4-B234-5AA317789503";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster13GroupParts";
	rename -uid "A23A5188-477C-364C-38E2-D7B423D42C0E";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:3]";
createNode objectSet -n "tweakSet13";
	rename -uid "F940948B-4EBA-1A76-8832-7EAF895BB854";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId26";
	rename -uid "E8ECBACC-4E61-0D67-ABA1-21ADDEF8C260";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts26";
	rename -uid "B821A384-4956-B458-D81A-46BA0DC64280";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster14";
	rename -uid "3B8E0D1E-4A3B-6636-B229-F5AAC75D8B86";
	setAttr ".skm" -1;
	setAttr -s 3 ".wl";
	setAttr ".wl[0:2].w"
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak14";
	rename -uid "17DD58A8-4265-1B48-9806-14BE39BA0004";
createNode objectSet -n "skinCluster14Set";
	rename -uid "494D6847-4A2D-7FA3-1CF3-2DAE3ED21E83";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster14GroupId";
	rename -uid "EB2C38C1-40CD-D24E-8F67-D0BEBD6D0F0B";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster14GroupParts";
	rename -uid "AE9AD2FA-48EE-0199-B579-57B97E54D92D";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:2]";
createNode objectSet -n "tweakSet14";
	rename -uid "CAF6459C-44B5-CDEA-E005-35AE06320DB6";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId28";
	rename -uid "5AF7E051-475B-59B0-37E5-44AC48064591";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts28";
	rename -uid "F8985E62-4A1D-2C89-7851-C7B0C9784734";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster15";
	rename -uid "1BD8ED81-4A98-77BD-F288-449C6D6D1DE4";
	setAttr ".skm" -1;
	setAttr -s 14 ".wl";
	setAttr ".wl[0:13].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak15";
	rename -uid "E2CFC66B-42F1-BD20-4936-1EA4CEEC5B6A";
createNode objectSet -n "skinCluster15Set";
	rename -uid "60163993-4A31-3C98-1AB8-71A293329BEA";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster15GroupId";
	rename -uid "FCAEBD47-43EE-2EDC-B0BF-329570487CEF";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster15GroupParts";
	rename -uid "3559D0E9-4E1C-D219-3747-1EAE91060458";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:13]";
createNode objectSet -n "tweakSet15";
	rename -uid "4A65619A-4DE3-9B84-9B8D-8FB3FEC5BD5B";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId30";
	rename -uid "38EAA4E8-4D3E-CB93-473E-F9A6D1F8A06D";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts30";
	rename -uid "B59B85CA-4993-BF5E-5F5C-90A582AA3486";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster16";
	rename -uid "42E7DD3E-4045-E63B-198C-A3AB0942B7A2";
	setAttr ".skm" -1;
	setAttr -s 5 ".wl";
	setAttr ".wl[0:4].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak16";
	rename -uid "F109AF43-4073-22BA-D0C5-B9AADC356894";
createNode objectSet -n "skinCluster16Set";
	rename -uid "FB5F8636-49DC-DF2D-9FBE-BCAFB8BBBEF2";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster16GroupId";
	rename -uid "DC8FBA21-4569-0381-9CAE-70B98F2A38C5";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster16GroupParts";
	rename -uid "D1826925-4815-056E-D25C-1DBC7B770D03";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:4]";
createNode objectSet -n "tweakSet16";
	rename -uid "7EDC997B-447D-B447-78A1-92A63F53FE10";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId32";
	rename -uid "6F060CB1-4B5B-4EE9-078F-8BBD01BE1CD1";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts32";
	rename -uid "D80F0764-481B-DC48-3983-B2A4F96FD1D8";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster17";
	rename -uid "04BE5EDD-4650-B864-8208-D7AD57BCB5AC";
	setAttr ".skm" -1;
	setAttr -s 8 ".wl";
	setAttr ".wl[0:7].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak17";
	rename -uid "9BED4D1A-4656-0741-D356-D6A3F2D85F9B";
createNode objectSet -n "skinCluster17Set";
	rename -uid "7A7F2B2D-40DF-C7D4-9592-578B03C3BEFC";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster17GroupId";
	rename -uid "52A98E17-438F-4D31-1F91-1180EEAB5DFF";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster17GroupParts";
	rename -uid "6A342F8E-4277-2FBF-23F1-4B8FFE4DF159";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:7]";
createNode objectSet -n "tweakSet17";
	rename -uid "7D561586-4FA6-7261-1212-C093738C1A3E";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId34";
	rename -uid "1AA152B6-4C19-EAF1-0BA6-19A4BC119BC3";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts34";
	rename -uid "774C8E66-4004-39E7-7BA6-F583D64D3E64";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster18";
	rename -uid "6E2E9D50-4D40-548B-DDF0-A49316AA9DC5";
	setAttr ".skm" -1;
	setAttr -s 6 ".wl";
	setAttr ".wl[0:5].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak18";
	rename -uid "2510C44A-4A10-E86E-3040-A49066D63310";
createNode objectSet -n "skinCluster18Set";
	rename -uid "1A6D8615-4732-A917-1F37-00815BB28E66";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster18GroupId";
	rename -uid "F91F4C48-42A1-ADE4-21CB-668025BB043E";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster18GroupParts";
	rename -uid "C22DA5B3-488B-5175-59CD-589400AD0FA9";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:5]";
createNode objectSet -n "tweakSet18";
	rename -uid "0E8FDC51-44DB-2C6F-0364-28B3AE491C8C";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId36";
	rename -uid "87D94C93-4315-7C92-5CBB-CEAD01BFCB1D";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts36";
	rename -uid "46D08DF4-4B4D-2C22-F0AB-0A9E2177E138";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster19";
	rename -uid "26C66BFF-4468-1D5D-DB8B-258D30A593D9";
	setAttr ".skm" -1;
	setAttr -s 6 ".wl";
	setAttr ".wl[0:5].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak19";
	rename -uid "5395C02A-4DFE-19E9-104F-53935F5562FC";
createNode objectSet -n "skinCluster19Set";
	rename -uid "5BD18BE7-4945-0A4D-E4D7-4EB6698EFE86";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster19GroupId";
	rename -uid "E1C8AFE0-4B10-D744-5AE5-98BC6675BFC5";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster19GroupParts";
	rename -uid "6528C267-4976-8616-5DEE-AC841CCD4366";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:5]";
createNode objectSet -n "tweakSet19";
	rename -uid "EDA4FD90-4D4F-3897-432F-BDA7D3F77862";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId38";
	rename -uid "1E47CA43-4EC7-6F24-14B0-C596236F6524";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts38";
	rename -uid "05A62606-4DA8-8E73-A10F-008B4364ED97";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster20";
	rename -uid "9BD1861A-403F-A30F-2896-E5B46EA9FEEF";
	setAttr ".skm" -1;
	setAttr -s 3 ".wl";
	setAttr ".wl[0:2].w"
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak20";
	rename -uid "27EBA389-4D73-E9AE-729B-D19C9271DAED";
createNode objectSet -n "skinCluster20Set";
	rename -uid "862F0E1E-46E2-36D2-A00B-1B8EBA0F9CF9";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster20GroupId";
	rename -uid "604DE39A-412B-129E-C34E-D689A80C3BC6";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster20GroupParts";
	rename -uid "D2DA45F3-488B-B665-1D40-629A21F7BFA9";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:2]";
createNode objectSet -n "tweakSet20";
	rename -uid "38573ED5-4053-03F6-88A0-0D8F5E49A84E";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId40";
	rename -uid "2F10875E-4C4E-4329-CBD7-4AAC1198F8A0";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts40";
	rename -uid "C2F35BDF-4323-7B76-F5D1-0DA83BA49383";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster21";
	rename -uid "F9449B1F-451A-256E-DEC6-2D928E2623A5";
	setAttr ".skm" -1;
	setAttr -s 4 ".wl";
	setAttr ".wl[0:3].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak21";
	rename -uid "624652A3-4F28-9191-096C-28A7B226B91D";
createNode objectSet -n "skinCluster21Set";
	rename -uid "CAB4F65D-4D42-70AE-5FB5-DCB55C7A610B";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster21GroupId";
	rename -uid "785D8D79-437A-CB64-C0B7-83A74EDB85A1";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster21GroupParts";
	rename -uid "10F7A0F6-4F06-3700-CE8F-FF9F1E7C4297";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:3]";
createNode objectSet -n "tweakSet21";
	rename -uid "755ED6ED-459E-1D7A-C230-439663EC26A1";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId42";
	rename -uid "7BF871EA-49B9-85B1-8FC0-029B971869EB";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts42";
	rename -uid "6CBFBDA0-4A2F-7600-799D-41B5E25A680F";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster22";
	rename -uid "9A9DCDD3-44D2-5AB0-CDBD-E29856B42025";
	setAttr ".skm" -1;
	setAttr -s 13 ".wl";
	setAttr ".wl[0:12].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak22";
	rename -uid "FA0E1F57-40E9-77F8-8DFD-9A96D0CC2A7A";
createNode objectSet -n "skinCluster22Set";
	rename -uid "F44A9745-429E-6407-29ED-0B948E6D4F99";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster22GroupId";
	rename -uid "469DA76D-4DCE-CE61-2305-90A5040D76FD";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster22GroupParts";
	rename -uid "99DEDCF7-41E6-1EB7-4368-6AA222CF3689";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:12]";
createNode objectSet -n "tweakSet22";
	rename -uid "AFAAA179-41B9-6D58-7ACB-378DCDF87C56";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId44";
	rename -uid "BBCDB3FF-4A67-C228-CB8A-ABA8BAF22EBE";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts44";
	rename -uid "EC3B6088-4DA9-D76F-13F3-95A4702863A9";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster23";
	rename -uid "72CECFAA-4887-693B-9ABC-DD9883FC393C";
	setAttr ".skm" -1;
	setAttr -s 18 ".wl";
	setAttr ".wl[0:17].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak23";
	rename -uid "127E5C1E-42E2-4DF2-7162-6788B6EB0DA3";
createNode objectSet -n "skinCluster23Set";
	rename -uid "C82FF728-4232-0446-FECF-8B8505B8FAC5";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster23GroupId";
	rename -uid "FAE304EE-433B-7738-0043-34BD568150BA";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster23GroupParts";
	rename -uid "D9940B06-4C6B-FE3C-ECF3-B8AC808497A7";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:17]";
createNode objectSet -n "tweakSet23";
	rename -uid "B4FF5FCC-4C64-2D76-9AC4-AC995EE437F0";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId46";
	rename -uid "C7565752-40F6-7227-F8E1-96BA55AB72CB";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts46";
	rename -uid "20C068AF-495E-B186-FA29-CEA586ADF62C";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster24";
	rename -uid "62054DA7-489E-D51C-3745-E48034836D6B";
	setAttr ".skm" -1;
	setAttr -s 8 ".wl";
	setAttr ".wl[0:7].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak24";
	rename -uid "B79C0D7A-4F27-BFCC-0A77-888CEE44450C";
createNode objectSet -n "skinCluster24Set";
	rename -uid "E37BD534-43E1-77B0-B247-33ABEF4F1EA6";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster24GroupId";
	rename -uid "9B727D41-40C6-A635-F848-4B93F9DCBEBA";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster24GroupParts";
	rename -uid "93752D3F-4FCF-31B0-B9F6-969CCB1E20FA";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:7]";
createNode objectSet -n "tweakSet24";
	rename -uid "72E79768-4AAD-82E4-E2B0-B297E4A24331";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId48";
	rename -uid "6D2C72EE-4F9A-0467-E153-E1926B043867";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts48";
	rename -uid "6902BD34-4EE9-EFCA-EC59-9886A15CDB76";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster25";
	rename -uid "59AC8D60-4666-207B-EB86-FABAE4B07FCB";
	setAttr ".skm" -1;
	setAttr -s 3 ".wl";
	setAttr ".wl[0:2].w"
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak25";
	rename -uid "10A862BA-4F37-FF39-A0CB-8BB78ECEEC05";
createNode objectSet -n "skinCluster25Set";
	rename -uid "60523BBF-406A-3862-18D0-E596B1E141D4";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster25GroupId";
	rename -uid "5B2F37FE-4B78-0887-DB1A-52850838BBE7";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster25GroupParts";
	rename -uid "85AC5196-4395-1FF4-3EC2-B68765C9EE96";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:2]";
createNode objectSet -n "tweakSet25";
	rename -uid "EF0A60E3-4163-7285-9B87-0BBC604E6074";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId50";
	rename -uid "8C552BF2-4791-A8B8-9864-09A9241DD08B";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts50";
	rename -uid "C821D3B6-4472-372E-756D-CDB43DD27173";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster26";
	rename -uid "13B8CC94-4879-A6FC-2818-3C97DE345207";
	setAttr ".skm" -1;
	setAttr -s 72 ".wl";
	setAttr ".wl[0:71].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak26";
	rename -uid "CEEAB427-489C-698B-6BE2-1EB45FB1F35F";
createNode objectSet -n "skinCluster26Set";
	rename -uid "16CABF7F-40FE-5517-8506-A98168F86AFD";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster26GroupId";
	rename -uid "038CB949-478D-7BA5-1D92-9C947695CF78";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster26GroupParts";
	rename -uid "C773C5A8-4A54-24D7-B6DD-EA86197AE6B3";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:71]";
createNode objectSet -n "tweakSet26";
	rename -uid "FBD8AB4D-435A-B0E8-C061-8FAFF7AC5134";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId52";
	rename -uid "3BF271E9-4A2A-AEF3-BD3A-AC9F8CAB67A6";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts52";
	rename -uid "705AF507-41BE-C9E7-D897-ACBCD06E7C80";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster27";
	rename -uid "EB991A43-4710-9D81-DB85-74A104AA200C";
	setAttr ".skm" -1;
	setAttr -s 6 ".wl";
	setAttr ".wl[0:5].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak27";
	rename -uid "11538CC8-4D1E-5CC1-F746-E58C0A7D2871";
createNode objectSet -n "skinCluster27Set";
	rename -uid "338B52A8-468C-AD15-7B2C-04AA42A9A864";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster27GroupId";
	rename -uid "28075D6A-46B7-D0F9-B2B5-4997EDE9CF55";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster27GroupParts";
	rename -uid "9908ABD2-41F2-1548-1F25-F69820FF64D6";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:5]";
createNode objectSet -n "tweakSet27";
	rename -uid "A73D1ED5-48D6-47DC-5B9B-D1B462D24BFE";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId54";
	rename -uid "829D1CD9-49A6-A191-7C78-93AD0F977639";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts54";
	rename -uid "144B4B63-4F4B-002C-6751-5D83EE03F94F";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster28";
	rename -uid "33C9CEA6-4A8B-605F-B24C-8A91E93C029F";
	setAttr ".skm" -1;
	setAttr -s 8 ".wl";
	setAttr ".wl[0:7].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak28";
	rename -uid "D4024529-40C8-EA66-A165-1DAD8BC56C05";
createNode objectSet -n "skinCluster28Set";
	rename -uid "ABA477F6-4E95-CCBC-5C31-8FB209C9B4DC";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster28GroupId";
	rename -uid "DEABBA95-401B-488A-F8CC-16A6EAD73E4B";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster28GroupParts";
	rename -uid "85B42848-4CF4-BA83-F5EB-13B6E709A76B";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:7]";
createNode objectSet -n "tweakSet28";
	rename -uid "F377A72B-4BA0-3F3C-57D3-6D80BD8BFE6D";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId56";
	rename -uid "308F572E-43CE-D3E0-A2A3-D596DD9B034E";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts56";
	rename -uid "DD31E6DB-4528-D10C-8360-35807B90061D";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster29";
	rename -uid "C19E7741-4C0C-6563-40F3-13A8006BFB4F";
	setAttr ".skm" -1;
	setAttr -s 25 ".wl";
	setAttr ".wl[0:24].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak29";
	rename -uid "B85FE19F-4FAF-47BD-86FB-0DA7A7604556";
createNode objectSet -n "skinCluster29Set";
	rename -uid "546524E3-4DDB-9840-B493-C980EE9A2C59";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster29GroupId";
	rename -uid "110F2DBD-4526-571B-09D6-B185689A7471";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster29GroupParts";
	rename -uid "549AE9EA-47CD-2E21-9C2B-17863FA64BBB";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:24]";
createNode objectSet -n "tweakSet29";
	rename -uid "4F827421-47AC-CCA9-4107-FF8BE0D7121E";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId58";
	rename -uid "73ACF0D5-4BF9-9C52-D549-3ABFD5D543C5";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts58";
	rename -uid "FFE7B320-49C2-9CEB-5BBB-0D95C127826D";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster30";
	rename -uid "E2AB782E-4818-8540-7615-F996DABAFF37";
	setAttr ".skm" -1;
	setAttr -s 10 ".wl";
	setAttr ".wl[0:9].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak30";
	rename -uid "0E8EE00B-4191-43FE-5BFE-22B763FDD1B8";
createNode objectSet -n "skinCluster30Set";
	rename -uid "1B984BDE-4833-4620-A24B-45847AF0B31B";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster30GroupId";
	rename -uid "BD6A04D2-4A5E-0FEE-2489-A799A5012EAB";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster30GroupParts";
	rename -uid "49546672-4EC4-3E20-6384-B491942EB32F";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:9]";
createNode objectSet -n "tweakSet30";
	rename -uid "5735C0A3-4D63-F7B4-05AB-B8A2B066C88E";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId60";
	rename -uid "940AFB25-4335-7EDC-5694-8BAD2542FE89";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts60";
	rename -uid "285D123D-4813-1DB6-9DA9-C4BDCC26BB93";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster31";
	rename -uid "D8B7AB11-43AD-2D45-6CC2-2C941AE035A8";
	setAttr ".skm" -1;
	setAttr -s 5 ".wl";
	setAttr ".wl[0:4].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak31";
	rename -uid "1EB218CA-428B-ED04-148F-CCB16298EC21";
createNode objectSet -n "skinCluster31Set";
	rename -uid "2E433144-4066-1090-7BE1-65B0F5D9C4CC";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster31GroupId";
	rename -uid "73FC7BA4-4EDA-DE5D-8254-E19A2800C5C9";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster31GroupParts";
	rename -uid "EC41AD74-445A-86FE-F574-6C9CC8A2A96A";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:4]";
createNode objectSet -n "tweakSet31";
	rename -uid "6DE719EC-4E4E-9555-F113-B190A660B1D1";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId62";
	rename -uid "719A809A-47FF-CEEC-651D-399B59B5C81E";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts62";
	rename -uid "01FFAD50-4752-D559-9C93-3C81D066CAFB";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster32";
	rename -uid "5A802D50-4D3E-74AF-0854-CE993B1FBFB5";
	setAttr ".skm" -1;
	setAttr -s 12 ".wl";
	setAttr ".wl[0:11].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak32";
	rename -uid "D7E4362C-4899-7030-F733-5887FF51A311";
createNode objectSet -n "skinCluster32Set";
	rename -uid "E3CF0871-49BC-4CF7-F7DC-519B66877D54";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster32GroupId";
	rename -uid "E57581B3-4C09-2D14-F804-4A84D7E9BA95";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster32GroupParts";
	rename -uid "DFC890D4-455C-9FDE-2125-6CA61903E44D";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:11]";
createNode objectSet -n "tweakSet32";
	rename -uid "8F3A4F26-4381-BC32-64E1-4BA186A9FFEB";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId64";
	rename -uid "030C3BE8-453E-C3F4-E251-0A9C3AAB0ED0";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts64";
	rename -uid "367E04C0-4257-59C5-BB13-54954BE54974";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster33";
	rename -uid "33D7CD43-4399-19E6-796C-EFBBDC0F254E";
	setAttr ".skm" -1;
	setAttr -s 14 ".wl";
	setAttr ".wl[0:13].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak33";
	rename -uid "DC8F93F0-4265-D3C9-D1C9-C6861547C6E8";
createNode objectSet -n "skinCluster33Set";
	rename -uid "3D1F3EC4-4187-D41B-E0E4-4B8F935202E2";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster33GroupId";
	rename -uid "5EA4C844-4EB3-49FB-9AF8-EDA119ADE005";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster33GroupParts";
	rename -uid "367A72D0-4638-3D66-5B10-129D05020DC1";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:13]";
createNode objectSet -n "tweakSet33";
	rename -uid "BD9A1E03-483F-AFAC-048C-24B7E459E5BB";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId66";
	rename -uid "05EF80A7-4A3F-8607-586F-C8BA26723298";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts66";
	rename -uid "CFCAAFB8-4D3A-EA55-D844-41851B993EA7";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster34";
	rename -uid "11041EB4-4CCE-80BE-3BB7-A09F089469EB";
	setAttr ".skm" -1;
	setAttr -s 24 ".wl";
	setAttr ".wl[0:23].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak34";
	rename -uid "A722C090-4F25-C070-1FDC-458B6BC0D44D";
createNode objectSet -n "skinCluster34Set";
	rename -uid "05AFBCB1-46E5-7399-F3E3-978DF2E84B4E";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster34GroupId";
	rename -uid "626FDBF9-4BB4-3D89-98C5-788CCD023AA9";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster34GroupParts";
	rename -uid "7DA01999-46F9-6173-C6F3-9C8004D8D991";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:23]";
createNode objectSet -n "tweakSet34";
	rename -uid "3B381951-4052-702E-A39D-9FBE1B947B99";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId68";
	rename -uid "99D7000D-42CF-4808-7D8B-4CA8EE8CD6A3";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts68";
	rename -uid "1F647FBC-43D9-A42A-6ED7-94AF82099A2F";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster35";
	rename -uid "5CFA5FE5-4494-5400-58A3-95B2C8893F70";
	setAttr ".skm" -1;
	setAttr -s 52 ".wl";
	setAttr ".wl[0:51].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak35";
	rename -uid "894E4D1D-424A-960F-67A8-98AD2A29550C";
createNode objectSet -n "skinCluster35Set";
	rename -uid "F0951B95-42B8-BB63-7F9D-02AE755E179F";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster35GroupId";
	rename -uid "392B3F57-468E-909B-397B-50A67AAE4187";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster35GroupParts";
	rename -uid "2D09DD30-4448-E206-87D8-CE9AA4E23F93";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:51]";
createNode objectSet -n "tweakSet35";
	rename -uid "E2FC108E-4652-70FF-D347-9790A6A0AF14";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId70";
	rename -uid "0F110A0C-4BBA-7642-9160-8C897B6D473F";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts70";
	rename -uid "B6258BA0-4112-8C10-E668-1AAF45680C6E";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster36";
	rename -uid "9D6C46CD-4298-7205-DDEE-98845957EBC9";
	setAttr ".skm" -1;
	setAttr -s 6 ".wl";
	setAttr ".wl[0:5].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak36";
	rename -uid "3955D37E-43A6-2BAD-D18F-F3A3BBF33F68";
createNode objectSet -n "skinCluster36Set";
	rename -uid "9D64787B-461D-DBD8-D64C-69B0048DF77B";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster36GroupId";
	rename -uid "1B4EFCB3-4D37-A3CC-D2C4-96900B5269E4";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster36GroupParts";
	rename -uid "7C67D9BB-4F63-39DB-7AF8-21B70219A3E9";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:5]";
createNode objectSet -n "tweakSet36";
	rename -uid "3F01EB97-401C-7B80-8D5D-98BCFB5F49A5";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId72";
	rename -uid "F1AF96C3-4CA9-D697-04C3-6C8979C116B4";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts72";
	rename -uid "6C317D90-4EAC-542A-720A-58AB9935EABE";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster37";
	rename -uid "3D2A1EBF-4804-71EA-6E67-9FBD70574140";
	setAttr ".skm" -1;
	setAttr -s 14 ".wl";
	setAttr ".wl[0:13].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak37";
	rename -uid "331D39EE-42CF-0ED9-24EB-A3A417901C69";
createNode objectSet -n "skinCluster37Set";
	rename -uid "9F795B22-46C1-4336-B46D-B395AE95D83D";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster37GroupId";
	rename -uid "5A1DD118-40BF-09BE-DB99-C7BCE672B036";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster37GroupParts";
	rename -uid "53FE62CC-48E6-8B41-C937-C79731A2A396";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:13]";
createNode objectSet -n "tweakSet37";
	rename -uid "20C0328F-48ED-FF35-8419-91A4377F1CBA";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId74";
	rename -uid "150DF96D-41DE-C0FA-A224-BA9685BCD689";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts74";
	rename -uid "E2BA0DB5-482D-3F4B-FCC3-3D934BD485F8";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster38";
	rename -uid "6DF17274-44A5-7A51-8BB7-BC993433A89E";
	setAttr ".skm" -1;
	setAttr -s 24 ".wl";
	setAttr ".wl[0:23].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak38";
	rename -uid "8DD0CD21-4689-3907-5B3C-13B2F2D6289E";
createNode objectSet -n "skinCluster38Set";
	rename -uid "EAE91AFF-4713-D2E3-DF68-A09BF4DAA821";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster38GroupId";
	rename -uid "944D25C3-4634-8854-659F-AE82A4CA0026";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster38GroupParts";
	rename -uid "8956247D-4BED-C761-CB56-8A955196CCD1";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:23]";
createNode objectSet -n "tweakSet38";
	rename -uid "CA5D7947-4A26-CB1B-3C07-C28D91DEE986";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId76";
	rename -uid "9090F840-4B56-499A-3959-F69F50EA96D1";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts76";
	rename -uid "E6A49AC1-4C85-6ACD-7204-6393AB9A45BC";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster39";
	rename -uid "A5BEB32C-4013-469A-DCB1-29B90543D328";
	setAttr ".skm" -1;
	setAttr -s 6 ".wl";
	setAttr ".wl[0:5].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak39";
	rename -uid "3A85D12E-4958-2AFF-68E3-B6B9AB89CB47";
createNode objectSet -n "skinCluster39Set";
	rename -uid "84F59FA7-432D-F456-9931-B9A758DC5DCC";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster39GroupId";
	rename -uid "B400E60E-4FB8-5697-481D-809B8B9EEF19";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster39GroupParts";
	rename -uid "628C0F17-47E0-1D7B-F375-37A7DB6505EA";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:5]";
createNode objectSet -n "tweakSet39";
	rename -uid "59264850-4F32-DA13-6BF8-DFBCB1AFAA1C";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId78";
	rename -uid "04F69CC6-482D-FDC1-644C-BC9F9EE0AB99";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts78";
	rename -uid "AE295E92-463C-8AE3-F98E-76BFFDAFF328";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster40";
	rename -uid "C9E001D4-4560-2455-0B97-1FA34BFF655C";
	setAttr ".skm" -1;
	setAttr -s 14 ".wl";
	setAttr ".wl[0:13].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak40";
	rename -uid "D6D2E2D1-4FB1-9D01-5FEE-05AC089615C4";
createNode objectSet -n "skinCluster40Set";
	rename -uid "4440BB52-49DB-DEC2-1FE8-DA80AA69085F";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster40GroupId";
	rename -uid "0981B612-4BED-D96A-0684-9AA46396EB8B";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster40GroupParts";
	rename -uid "DDF2302A-485E-A51C-056B-2FB986B6EB5F";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:13]";
createNode objectSet -n "tweakSet40";
	rename -uid "A1927886-4D6E-323D-63DA-2BB472D79E39";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId80";
	rename -uid "F3DEDBA5-444D-FD20-EBAB-549D12DE762A";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts80";
	rename -uid "19373507-4C57-88FE-2F73-D5AC36371FCB";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster41";
	rename -uid "C59A3962-427A-06E5-7EF3-BE83C1A2ABC7";
	setAttr ".skm" -1;
	setAttr -s 24 ".wl";
	setAttr ".wl[0:23].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak41";
	rename -uid "08A10379-46A2-7D76-4038-A78552971545";
createNode objectSet -n "skinCluster41Set";
	rename -uid "39AB4617-476E-0BFE-5BDC-B884FB87F146";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster41GroupId";
	rename -uid "4B9A7755-42C3-981F-054E-D3B7D415CA27";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster41GroupParts";
	rename -uid "A08C0E5C-460A-C884-92EA-4D943ECCFD96";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:23]";
createNode objectSet -n "tweakSet41";
	rename -uid "BD0BFB24-4131-73A1-D695-8E86A6BBE8CA";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId82";
	rename -uid "5D00A577-471C-4E4C-50E4-459377F21E32";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts82";
	rename -uid "AD88CB83-4239-A991-F796-4BAE8A093468";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster42";
	rename -uid "EE052B54-4108-016A-944D-7FB72500715C";
	setAttr ".skm" -1;
	setAttr -s 6 ".wl";
	setAttr ".wl[0:5].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak42";
	rename -uid "08A88203-4794-B859-1BAB-6FB32F8250DC";
createNode objectSet -n "skinCluster42Set";
	rename -uid "A14CFCBF-41F7-7AD7-FB5D-4E9EA3B8C53D";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster42GroupId";
	rename -uid "477CD546-4E91-E67C-48A6-BF8873177C25";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster42GroupParts";
	rename -uid "4A351913-43CB-3528-1D70-B0910C538B49";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:5]";
createNode objectSet -n "tweakSet42";
	rename -uid "A8E9C755-4D78-80C9-DC8A-F784C9559DBB";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId84";
	rename -uid "4AFF27A3-4550-D389-E040-C8AEAF9C647F";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts84";
	rename -uid "498041BA-4146-8CE6-1760-2CA30CFD7509";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster43";
	rename -uid "E63C80C4-420B-5148-93EB-90B86AFF5A44";
	setAttr ".skm" -1;
	setAttr -s 14 ".wl";
	setAttr ".wl[0:13].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak43";
	rename -uid "CB4E3883-4B57-6619-CBA4-E1A4FF3D2949";
createNode objectSet -n "skinCluster43Set";
	rename -uid "8CF4C325-47E3-4C6F-3A49-46A50AD14E49";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster43GroupId";
	rename -uid "7A7E6C52-42FA-CC1A-E035-B1AFE5196458";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster43GroupParts";
	rename -uid "BDC4890C-42DF-D0CF-EF3F-22B0797EF9CF";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:13]";
createNode objectSet -n "tweakSet43";
	rename -uid "EF9B07FC-42DC-B1E9-DA2B-2FA3C911CD6C";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId86";
	rename -uid "99F20238-45CA-002B-DEAF-4C8206A7A0C0";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts86";
	rename -uid "30D4D977-40E2-3AF6-10CA-9084EBF6B151";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster44";
	rename -uid "7759D960-4D8F-4B13-F90D-248A9AA9BFD0";
	setAttr ".skm" -1;
	setAttr -s 24 ".wl";
	setAttr ".wl[0:23].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak44";
	rename -uid "3F049384-4E90-871D-39AF-6E950D5AA650";
createNode objectSet -n "skinCluster44Set";
	rename -uid "358E57A5-4816-F1D4-2E9D-1C88AC4CA797";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster44GroupId";
	rename -uid "211DE776-40E0-AE4F-0BAD-7FAD4AB973FC";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster44GroupParts";
	rename -uid "5A1F01FD-46AC-38BF-9995-F880D0F9BB69";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:23]";
createNode objectSet -n "tweakSet44";
	rename -uid "FA3D38AB-4973-A5FE-3517-A181E10F5E8B";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId88";
	rename -uid "2F73A887-4942-F7F7-317B-3D8CD57D7AA8";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts88";
	rename -uid "08E7FFFE-4C9B-5651-CA9B-B994B7CEA7E3";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster45";
	rename -uid "0EC18E94-4DB6-CA42-9881-96A268975034";
	setAttr ".skm" -1;
	setAttr -s 6 ".wl";
	setAttr ".wl[0:5].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak45";
	rename -uid "E321BCA7-470B-AF0F-4FF0-C1A39AC2E849";
createNode objectSet -n "skinCluster45Set";
	rename -uid "B8B6B2BC-4C3D-FA23-93CB-84A3175419DD";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster45GroupId";
	rename -uid "BDAAA071-445B-DF39-D1A3-CF8873058C08";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster45GroupParts";
	rename -uid "D7376254-4C36-F1DF-6F6A-929449E20F1A";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:5]";
createNode objectSet -n "tweakSet45";
	rename -uid "F562B6EE-4A24-CD17-621A-E99CFB61E9B8";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId90";
	rename -uid "D7C99190-411B-52BB-EFC4-8B85E76B000F";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts90";
	rename -uid "F740A69C-4FCA-46B2-B716-92AEBD9ADD3A";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster46";
	rename -uid "0DE28B55-42A7-B223-33C2-FDB6B15F6AAC";
	setAttr ".skm" -1;
	setAttr -s 42 ".wl";
	setAttr ".wl[0:41].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak46";
	rename -uid "1FF18AAF-4820-6499-786F-37BDA8006A47";
createNode objectSet -n "skinCluster46Set";
	rename -uid "E777440D-4E6C-F192-F981-3C8A452A58B0";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster46GroupId";
	rename -uid "04933B1C-409D-1A54-E6B3-089CDA03F688";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster46GroupParts";
	rename -uid "CB0E5123-4BFD-E8DC-4B01-F6960B86CDA9";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:41]";
createNode objectSet -n "tweakSet46";
	rename -uid "83A10FA9-46F3-FB42-9F58-BBA57064776D";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId92";
	rename -uid "0CA1C5EB-4305-935C-B69D-8DA6B6228942";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts92";
	rename -uid "FA624A14-4F97-96E6-CB1F-6B80303BAE42";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster47";
	rename -uid "E08730BB-4F85-EBEF-A6FF-5D8289105520";
	setAttr ".skm" -1;
	setAttr -s 81 ".wl";
	setAttr ".wl[0:80].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak47";
	rename -uid "B7E62DD7-453E-90FD-857E-4396305FA7A7";
createNode objectSet -n "skinCluster47Set";
	rename -uid "30962245-4AF2-6A37-EFFE-8DA273FE0460";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster47GroupId";
	rename -uid "E7480F1E-40B8-FDB3-9271-60A5BE4009F5";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster47GroupParts";
	rename -uid "1429C912-4724-3856-093C-8892D8D4C971";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:80]";
createNode objectSet -n "tweakSet47";
	rename -uid "9D3FB342-4906-3D24-AFEE-2D97FCF91994";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId94";
	rename -uid "0FFAA5C3-4071-730F-872C-CF9F026E3305";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts94";
	rename -uid "524B13BC-4A6A-5325-5EFC-4A9DE9AFA9B8";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster48";
	rename -uid "E0B99BC9-4A17-630F-7974-02881F52C0C7";
	setAttr ".skm" -1;
	setAttr -s 81 ".wl";
	setAttr ".wl[0:80].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak48";
	rename -uid "589AF389-473A-0200-4348-91BB3C7A5305";
createNode objectSet -n "skinCluster48Set";
	rename -uid "E403160A-46B3-5E3E-2562-C2912AF2AC02";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster48GroupId";
	rename -uid "5842D69B-45E9-75E3-3C4B-4AAB05D2EEC0";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster48GroupParts";
	rename -uid "B49409E4-4588-C444-0C76-F49499098B4F";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:80]";
createNode objectSet -n "tweakSet48";
	rename -uid "5DD9C7B7-4C31-57B7-E8D8-C48C1B2BE4B0";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId96";
	rename -uid "FE6240A8-4122-3D86-5034-EA928621B4FE";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts96";
	rename -uid "1C631D57-42EA-1C1F-E788-0883CEBD940D";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster49";
	rename -uid "457860AE-4D67-D3EE-AA40-C2AB71C52A3B";
	setAttr ".skm" -1;
	setAttr -s 81 ".wl";
	setAttr ".wl[0:80].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak49";
	rename -uid "222FFAFA-4CF3-25E3-BD9D-78A8581DF16A";
createNode objectSet -n "skinCluster49Set";
	rename -uid "9EB8F8C0-4CEE-6CC6-C516-2E8DB1E40E2B";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster49GroupId";
	rename -uid "E0CC5D19-4A83-E579-8F08-86A44D65D0E4";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster49GroupParts";
	rename -uid "D53CF098-4029-EBB3-50C2-099BB44ABF63";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:80]";
createNode objectSet -n "tweakSet49";
	rename -uid "2C39073B-47BD-9A17-B10C-65879C291F43";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId98";
	rename -uid "FD7EF8AE-4D0F-7DEA-AB0C-238743AD5058";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts98";
	rename -uid "6E5C0590-47DA-2056-A9D2-6F963E226A7B";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster50";
	rename -uid "C63DA6B2-442C-942D-2D61-7C8E4F855B24";
	setAttr ".skm" -1;
	setAttr -s 81 ".wl";
	setAttr ".wl[0:80].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak50";
	rename -uid "C39A3B16-4ED6-5863-9615-AE8B7120504E";
createNode objectSet -n "skinCluster50Set";
	rename -uid "16E36FAA-4023-B03F-254B-AD9DCAE839CD";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster50GroupId";
	rename -uid "31CB7DD7-4EB0-4577-CB09-88AAA2F22122";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster50GroupParts";
	rename -uid "4FA5FA3C-4D54-1015-EE06-8193B0F8AF64";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:80]";
createNode objectSet -n "tweakSet50";
	rename -uid "D1F62108-4176-023C-B65B-CBA368FA541A";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId100";
	rename -uid "485699A9-4E0E-8E3F-CDDB-B6966F8C0835";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts100";
	rename -uid "3EAEE721-4175-699E-FC3D-F281DB1CA5E8";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster51";
	rename -uid "957C1334-4F26-F31A-68B8-849455E8E16A";
	setAttr ".skm" -1;
	setAttr -s 12 ".wl";
	setAttr ".wl[0:11].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak51";
	rename -uid "C68AFEEB-47D5-C482-A78B-ACB5DAB9435B";
createNode objectSet -n "skinCluster51Set";
	rename -uid "29535E3F-4369-9B5C-5DE1-1D82B5C714C5";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster51GroupId";
	rename -uid "3195D413-4331-D4FA-E689-93BB629D703B";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster51GroupParts";
	rename -uid "90B8F1AD-4922-66F5-6D6A-58A34638923B";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:11]";
createNode objectSet -n "tweakSet51";
	rename -uid "EDEB5836-4865-DE85-1B40-D7BE647D7826";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId102";
	rename -uid "18C89B3D-41E8-9C3D-675B-61B03F7E7892";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts102";
	rename -uid "3C9B1347-496C-A6C1-0A1D-5B8ABD44F99E";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster52";
	rename -uid "07FE3C7F-4F6E-5097-2857-93996D6FF5EC";
	setAttr ".skm" -1;
	setAttr -s 8 ".wl";
	setAttr ".wl[0:7].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak52";
	rename -uid "AA349996-4EB7-5DA9-8F87-7986B76B200D";
createNode objectSet -n "skinCluster52Set";
	rename -uid "24C5A0EE-44B8-EC64-530A-A8A4F1BAB4F2";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster52GroupId";
	rename -uid "ED10E38D-4C99-CD28-0F89-0290D2C57A2C";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster52GroupParts";
	rename -uid "0750B01F-40EF-832A-6B47-B1BBF3A6158F";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:7]";
createNode objectSet -n "tweakSet52";
	rename -uid "CE7D2B17-4ED4-2889-9902-11927BB3E313";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId104";
	rename -uid "9404F571-470E-3352-E6F1-E7ABBD6D2063";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts104";
	rename -uid "BF7C626B-42E1-75EF-6715-9DA0BB328F74";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster53";
	rename -uid "B0C9090E-477B-1FA5-117E-5EB7268C7A52";
	setAttr ".skm" -1;
	setAttr -s 25 ".wl";
	setAttr ".wl[0:24].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak53";
	rename -uid "CC108777-40F2-6FF1-7384-CE99F088D564";
createNode objectSet -n "skinCluster53Set";
	rename -uid "53ABD1E9-4E60-ECD0-698B-AFADE3085542";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster53GroupId";
	rename -uid "836CEF96-40D5-E858-4957-AA8C8E5C4DDF";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster53GroupParts";
	rename -uid "7DC97236-499B-C5C7-EE98-5CAC67AB3F47";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:24]";
createNode objectSet -n "tweakSet53";
	rename -uid "00A03E33-4068-67C8-9193-DEA57678A21A";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId106";
	rename -uid "312F8814-4EEA-D0B6-737A-DA939CEC9EDE";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts106";
	rename -uid "667FDEA5-4549-C3F7-A9C6-13BBEEDE822B";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode skinCluster -n "skinCluster54";
	rename -uid "5DE26827-4F8A-A1E0-D325-33BCA8077538";
	setAttr ".skm" -1;
	setAttr -s 25 ".wl";
	setAttr ".wl[0:24].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr -s 2 ".pm";
	setAttr ".pm[0]" -type "matrix" 0.62044299999999997 0.45949499999999999 -0.63554299999999997 0
		 -0.57183700000000004 0.81964800000000004 0.034350899999999997 0 0.53670600000000002 0.34211399999999997 0.77130100000000001 0
		 4.6337780000000004 -5.8934189999999997 4.3996899999999997 1;
	setAttr ".pm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 2 ".ma";
	setAttr -s 2 ".dpf[0:1]"  4 4;
	setAttr -s 2 ".lw";
	setAttr -s 2 ".lw";
	setAttr ".mi" 5;
	setAttr ".bm" 1;
	setAttr ".ucm" yes;
	setAttr -s 2 ".ifcl";
	setAttr -s 2 ".ifcl";
createNode tweak -n "tweak54";
	rename -uid "2A0EA820-41F6-CFB5-6C3F-AA81BB8C2F51";
createNode objectSet -n "skinCluster54Set";
	rename -uid "6F79A26A-4362-30A5-DF3C-D996099FBD1C";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "skinCluster54GroupId";
	rename -uid "168785D3-4A5B-B3B2-7F41-E0ACAFB1CD82";
	setAttr ".ihi" 0;
createNode groupParts -n "skinCluster54GroupParts";
	rename -uid "2E4C8582-43FF-8666-3C2E-168F274A19BD";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[0:24]";
createNode objectSet -n "tweakSet54";
	rename -uid "D1D8F126-4612-9F4B-D9EE-AFA2EE775E7D";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId108";
	rename -uid "E374AD85-45F4-6E9D-0A50-798E0F73ECAD";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts108";
	rename -uid "F8325A12-4269-8636-6175-7A8024739960";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode animCurveTL -n "JOBJ_1_translateX";
	rename -uid "90DC83C9-4265-2460-7845-A19782B07D7D";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  0 2.6291899681091309;
createNode animCurveTL -n "JOBJ_1_translateY";
	rename -uid "6E6DD30B-4B70-D9A3-DB5F-FE8D82F290D3";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  0 3.115072697309766;
createNode animCurveTL -n "JOBJ_1_translateZ";
	rename -uid "80F272C4-453A-6A10-18DD-009E24A9F496";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  0 -3.8642399311065674;
createNode animCurveTU -n "JOBJ_1_visibility";
	rename -uid "71BFF5A4-4D06-C408-0EC1-58BE79BECBAB";
	setAttr ".tan" 9;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  0 1;
	setAttr ".kot[0]"  5;
createNode animCurveTA -n "JOBJ_1_rotateX";
	rename -uid "1F624E17-44FA-6179-02D1-94B6CD7B1FFE";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  0 3.9737229733538251;
createNode animCurveTA -n "JOBJ_1_rotateY";
	rename -uid "1F725730-4FED-D658-7471-03A65A88C77A";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  0 -35.288013422303329;
createNode animCurveTA -n "JOBJ_1_rotateZ";
	rename -uid "8FE51D82-4E1D-1ED1-C892-82BC6B9D177C";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  0 -0.15555660833149304;
createNode animCurveTU -n "JOBJ_1_scaleX";
	rename -uid "2C65B016-4E45-8371-A98B-33916D4B6EB6";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  0 1.0000002006269799;
createNode animCurveTU -n "JOBJ_1_scaleY";
	rename -uid "FD7FE4D0-47B2-640A-2091-7B9244C60455";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  0 1.0000002439624702;
createNode animCurveTU -n "JOBJ_1_scaleZ";
	rename -uid "61402FBD-46A7-3E27-8AEC-2296B64EFF1D";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  0 1.000000064325498;
createNode script -n "sceneConfigurationScriptNode";
	rename -uid "3104208C-417B-BAB3-A445-CABD8550E1E6";
	setAttr ".b" -type "string" "playbackOptions -min 0 -max 30 -ast 0 -aet 30 ";
	setAttr ".st" 6;
select -ne :time1;
	setAttr ".o" 0;
select -ne :hardwareRenderingGlobals;
	setAttr ".otfna" -type "stringArray" 22 "NURBS Curves" "NURBS Surfaces" "Polygons" "Subdiv Surface" "Particles" "Particle Instance" "Fluids" "Strokes" "Image Planes" "UI" "Lights" "Cameras" "Locators" "Joints" "IK Handles" "Deformers" "Motion Trails" "Components" "Hair Systems" "Follicles" "Misc. UI" "Ornaments"  ;
	setAttr ".otfva" -type "Int32Array" 22 0 1 1 1 1 1
		 1 1 1 0 0 0 0 0 0 0 0 0
		 0 0 0 0 ;
	setAttr ".fprt" yes;
select -ne :renderPartition;
	setAttr -s 56 ".st";
select -ne :renderGlobalsList1;
select -ne :defaultShaderList1;
	setAttr -s 58 ".s";
select -ne :postProcessList1;
	setAttr -s 2 ".p";
select -ne :defaultRenderUtilityList1;
	setAttr -s 54 ".u";
select -ne :defaultRenderingList1;
select -ne :defaultTextureList1;
	setAttr -s 54 ".tx";
select -ne :initialShadingGroup;
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :defaultRenderGlobals;
	setAttr ".fs" 0.5;
	setAttr ".ef" 5;
select -ne :defaultResolution;
	setAttr ".pa" 1;
select -ne :hardwareRenderGlobals;
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
connectAttr "JOBJ_0.s" "JOBJ_1.is";
connectAttr "JOBJ_1_translateX.o" "JOBJ_1.tx";
connectAttr "JOBJ_1_translateY.o" "JOBJ_1.ty";
connectAttr "JOBJ_1_translateZ.o" "JOBJ_1.tz";
connectAttr "JOBJ_1_visibility.o" "JOBJ_1.v";
connectAttr "JOBJ_1_rotateX.o" "JOBJ_1.rx";
connectAttr "JOBJ_1_rotateY.o" "JOBJ_1.ry";
connectAttr "JOBJ_1_rotateZ.o" "JOBJ_1.rz";
connectAttr "JOBJ_1_scaleX.o" "JOBJ_1.sx";
connectAttr "JOBJ_1_scaleY.o" "JOBJ_1.sy";
connectAttr "JOBJ_1_scaleZ.o" "JOBJ_1.sz";
connectAttr "skinCluster1GroupId.id" "Joint_1_Object_0_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster1Set.mwc" "Joint_1_Object_0_SINGLEShape.iog.og[0].gco";
connectAttr "groupId2.id" "Joint_1_Object_0_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet1.mwc" "Joint_1_Object_0_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster1.og[0]" "Joint_1_Object_0_SINGLEShape.i";
connectAttr "tweak1.vl[0].vt[0]" "Joint_1_Object_0_SINGLEShape.twl";
connectAttr "skinCluster2GroupId.id" "Joint_1_Object_1_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster2Set.mwc" "Joint_1_Object_1_SINGLEShape.iog.og[0].gco";
connectAttr "groupId4.id" "Joint_1_Object_1_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet2.mwc" "Joint_1_Object_1_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster2.og[0]" "Joint_1_Object_1_SINGLEShape.i";
connectAttr "tweak2.vl[0].vt[0]" "Joint_1_Object_1_SINGLEShape.twl";
connectAttr "skinCluster13GroupId.id" "Joint_1_Object_2_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster13Set.mwc" "Joint_1_Object_2_SINGLEShape.iog.og[0].gco";
connectAttr "groupId26.id" "Joint_1_Object_2_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet13.mwc" "Joint_1_Object_2_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster13.og[0]" "Joint_1_Object_2_SINGLEShape.i";
connectAttr "tweak13.vl[0].vt[0]" "Joint_1_Object_2_SINGLEShape.twl";
connectAttr "skinCluster24GroupId.id" "Joint_1_Object_3_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster24Set.mwc" "Joint_1_Object_3_SINGLEShape.iog.og[0].gco";
connectAttr "groupId48.id" "Joint_1_Object_3_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet24.mwc" "Joint_1_Object_3_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster24.og[0]" "Joint_1_Object_3_SINGLEShape.i";
connectAttr "tweak24.vl[0].vt[0]" "Joint_1_Object_3_SINGLEShape.twl";
connectAttr "skinCluster35GroupId.id" "Joint_1_Object_4_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster35Set.mwc" "Joint_1_Object_4_SINGLEShape.iog.og[0].gco";
connectAttr "groupId70.id" "Joint_1_Object_4_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet35.mwc" "Joint_1_Object_4_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster35.og[0]" "Joint_1_Object_4_SINGLEShape.i";
connectAttr "tweak35.vl[0].vt[0]" "Joint_1_Object_4_SINGLEShape.twl";
connectAttr "skinCluster46GroupId.id" "Joint_1_Object_5_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster46Set.mwc" "Joint_1_Object_5_SINGLEShape.iog.og[0].gco";
connectAttr "groupId92.id" "Joint_1_Object_5_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet46.mwc" "Joint_1_Object_5_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster46.og[0]" "Joint_1_Object_5_SINGLEShape.i";
connectAttr "tweak46.vl[0].vt[0]" "Joint_1_Object_5_SINGLEShape.twl";
connectAttr "skinCluster51GroupId.id" "Joint_1_Object_6_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster51Set.mwc" "Joint_1_Object_6_SINGLEShape.iog.og[0].gco";
connectAttr "groupId102.id" "Joint_1_Object_6_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet51.mwc" "Joint_1_Object_6_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster51.og[0]" "Joint_1_Object_6_SINGLEShape.i";
connectAttr "tweak51.vl[0].vt[0]" "Joint_1_Object_6_SINGLEShape.twl";
connectAttr "skinCluster52GroupId.id" "Joint_1_Object_7_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster52Set.mwc" "Joint_1_Object_7_SINGLEShape.iog.og[0].gco";
connectAttr "groupId104.id" "Joint_1_Object_7_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet52.mwc" "Joint_1_Object_7_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster52.og[0]" "Joint_1_Object_7_SINGLEShape.i";
connectAttr "tweak52.vl[0].vt[0]" "Joint_1_Object_7_SINGLEShape.twl";
connectAttr "skinCluster53GroupId.id" "Joint_1_Object_8_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster53Set.mwc" "Joint_1_Object_8_SINGLEShape.iog.og[0].gco";
connectAttr "groupId106.id" "Joint_1_Object_8_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet53.mwc" "Joint_1_Object_8_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster53.og[0]" "Joint_1_Object_8_SINGLEShape.i";
connectAttr "tweak53.vl[0].vt[0]" "Joint_1_Object_8_SINGLEShape.twl";
connectAttr "skinCluster54GroupId.id" "Joint_1_Object_9_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster54Set.mwc" "Joint_1_Object_9_SINGLEShape.iog.og[0].gco";
connectAttr "groupId108.id" "Joint_1_Object_9_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet54.mwc" "Joint_1_Object_9_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster54.og[0]" "Joint_1_Object_9_SINGLEShape.i";
connectAttr "tweak54.vl[0].vt[0]" "Joint_1_Object_9_SINGLEShape.twl";
connectAttr "skinCluster3GroupId.id" "Joint_1_Object_10_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster3Set.mwc" "Joint_1_Object_10_SINGLEShape.iog.og[0].gco";
connectAttr "groupId6.id" "Joint_1_Object_10_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet3.mwc" "Joint_1_Object_10_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster3.og[0]" "Joint_1_Object_10_SINGLEShape.i";
connectAttr "tweak3.vl[0].vt[0]" "Joint_1_Object_10_SINGLEShape.twl";
connectAttr "skinCluster4GroupId.id" "Joint_1_Object_11_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster4Set.mwc" "Joint_1_Object_11_SINGLEShape.iog.og[0].gco";
connectAttr "groupId8.id" "Joint_1_Object_11_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet4.mwc" "Joint_1_Object_11_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster4.og[0]" "Joint_1_Object_11_SINGLEShape.i";
connectAttr "tweak4.vl[0].vt[0]" "Joint_1_Object_11_SINGLEShape.twl";
connectAttr "skinCluster5GroupId.id" "Joint_1_Object_12_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster5Set.mwc" "Joint_1_Object_12_SINGLEShape.iog.og[0].gco";
connectAttr "groupId10.id" "Joint_1_Object_12_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet5.mwc" "Joint_1_Object_12_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster5.og[0]" "Joint_1_Object_12_SINGLEShape.i";
connectAttr "tweak5.vl[0].vt[0]" "Joint_1_Object_12_SINGLEShape.twl";
connectAttr "skinCluster6GroupId.id" "Joint_1_Object_13_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster6Set.mwc" "Joint_1_Object_13_SINGLEShape.iog.og[0].gco";
connectAttr "groupId12.id" "Joint_1_Object_13_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet6.mwc" "Joint_1_Object_13_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster6.og[0]" "Joint_1_Object_13_SINGLEShape.i";
connectAttr "tweak6.vl[0].vt[0]" "Joint_1_Object_13_SINGLEShape.twl";
connectAttr "skinCluster7GroupId.id" "Joint_1_Object_14_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster7Set.mwc" "Joint_1_Object_14_SINGLEShape.iog.og[0].gco";
connectAttr "groupId14.id" "Joint_1_Object_14_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet7.mwc" "Joint_1_Object_14_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster7.og[0]" "Joint_1_Object_14_SINGLEShape.i";
connectAttr "tweak7.vl[0].vt[0]" "Joint_1_Object_14_SINGLEShape.twl";
connectAttr "skinCluster8GroupId.id" "Joint_1_Object_15_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster8Set.mwc" "Joint_1_Object_15_SINGLEShape.iog.og[0].gco";
connectAttr "groupId16.id" "Joint_1_Object_15_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet8.mwc" "Joint_1_Object_15_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster8.og[0]" "Joint_1_Object_15_SINGLEShape.i";
connectAttr "tweak8.vl[0].vt[0]" "Joint_1_Object_15_SINGLEShape.twl";
connectAttr "skinCluster9GroupId.id" "Joint_1_Object_16_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster9Set.mwc" "Joint_1_Object_16_SINGLEShape.iog.og[0].gco";
connectAttr "groupId18.id" "Joint_1_Object_16_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet9.mwc" "Joint_1_Object_16_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster9.og[0]" "Joint_1_Object_16_SINGLEShape.i";
connectAttr "tweak9.vl[0].vt[0]" "Joint_1_Object_16_SINGLEShape.twl";
connectAttr "skinCluster10GroupId.id" "Joint_1_Object_17_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster10Set.mwc" "Joint_1_Object_17_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId20.id" "Joint_1_Object_17_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet10.mwc" "Joint_1_Object_17_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster10.og[0]" "Joint_1_Object_17_SINGLEShape.i";
connectAttr "tweak10.vl[0].vt[0]" "Joint_1_Object_17_SINGLEShape.twl";
connectAttr "skinCluster11GroupId.id" "Joint_1_Object_18_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster11Set.mwc" "Joint_1_Object_18_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId22.id" "Joint_1_Object_18_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet11.mwc" "Joint_1_Object_18_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster11.og[0]" "Joint_1_Object_18_SINGLEShape.i";
connectAttr "tweak11.vl[0].vt[0]" "Joint_1_Object_18_SINGLEShape.twl";
connectAttr "skinCluster12GroupId.id" "Joint_1_Object_19_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster12Set.mwc" "Joint_1_Object_19_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId24.id" "Joint_1_Object_19_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet12.mwc" "Joint_1_Object_19_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster12.og[0]" "Joint_1_Object_19_SINGLEShape.i";
connectAttr "tweak12.vl[0].vt[0]" "Joint_1_Object_19_SINGLEShape.twl";
connectAttr "skinCluster14GroupId.id" "Joint_1_Object_20_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster14Set.mwc" "Joint_1_Object_20_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId28.id" "Joint_1_Object_20_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet14.mwc" "Joint_1_Object_20_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster14.og[0]" "Joint_1_Object_20_SINGLEShape.i";
connectAttr "tweak14.vl[0].vt[0]" "Joint_1_Object_20_SINGLEShape.twl";
connectAttr "skinCluster15GroupId.id" "Joint_1_Object_21_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster15Set.mwc" "Joint_1_Object_21_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId30.id" "Joint_1_Object_21_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet15.mwc" "Joint_1_Object_21_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster15.og[0]" "Joint_1_Object_21_SINGLEShape.i";
connectAttr "tweak15.vl[0].vt[0]" "Joint_1_Object_21_SINGLEShape.twl";
connectAttr "skinCluster16GroupId.id" "Joint_1_Object_22_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster16Set.mwc" "Joint_1_Object_22_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId32.id" "Joint_1_Object_22_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet16.mwc" "Joint_1_Object_22_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster16.og[0]" "Joint_1_Object_22_SINGLEShape.i";
connectAttr "tweak16.vl[0].vt[0]" "Joint_1_Object_22_SINGLEShape.twl";
connectAttr "skinCluster17GroupId.id" "Joint_1_Object_23_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster17Set.mwc" "Joint_1_Object_23_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId34.id" "Joint_1_Object_23_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet17.mwc" "Joint_1_Object_23_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster17.og[0]" "Joint_1_Object_23_SINGLEShape.i";
connectAttr "tweak17.vl[0].vt[0]" "Joint_1_Object_23_SINGLEShape.twl";
connectAttr "skinCluster18GroupId.id" "Joint_1_Object_24_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster18Set.mwc" "Joint_1_Object_24_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId36.id" "Joint_1_Object_24_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet18.mwc" "Joint_1_Object_24_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster18.og[0]" "Joint_1_Object_24_SINGLEShape.i";
connectAttr "tweak18.vl[0].vt[0]" "Joint_1_Object_24_SINGLEShape.twl";
connectAttr "skinCluster19GroupId.id" "Joint_1_Object_25_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster19Set.mwc" "Joint_1_Object_25_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId38.id" "Joint_1_Object_25_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet19.mwc" "Joint_1_Object_25_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster19.og[0]" "Joint_1_Object_25_SINGLEShape.i";
connectAttr "tweak19.vl[0].vt[0]" "Joint_1_Object_25_SINGLEShape.twl";
connectAttr "skinCluster20GroupId.id" "Joint_1_Object_26_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster20Set.mwc" "Joint_1_Object_26_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId40.id" "Joint_1_Object_26_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet20.mwc" "Joint_1_Object_26_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster20.og[0]" "Joint_1_Object_26_SINGLEShape.i";
connectAttr "tweak20.vl[0].vt[0]" "Joint_1_Object_26_SINGLEShape.twl";
connectAttr "skinCluster21GroupId.id" "Joint_1_Object_27_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster21Set.mwc" "Joint_1_Object_27_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId42.id" "Joint_1_Object_27_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet21.mwc" "Joint_1_Object_27_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster21.og[0]" "Joint_1_Object_27_SINGLEShape.i";
connectAttr "tweak21.vl[0].vt[0]" "Joint_1_Object_27_SINGLEShape.twl";
connectAttr "skinCluster22GroupId.id" "Joint_1_Object_28_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster22Set.mwc" "Joint_1_Object_28_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId44.id" "Joint_1_Object_28_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet22.mwc" "Joint_1_Object_28_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster22.og[0]" "Joint_1_Object_28_SINGLEShape.i";
connectAttr "tweak22.vl[0].vt[0]" "Joint_1_Object_28_SINGLEShape.twl";
connectAttr "skinCluster23GroupId.id" "Joint_1_Object_29_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster23Set.mwc" "Joint_1_Object_29_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId46.id" "Joint_1_Object_29_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet23.mwc" "Joint_1_Object_29_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster23.og[0]" "Joint_1_Object_29_SINGLEShape.i";
connectAttr "tweak23.vl[0].vt[0]" "Joint_1_Object_29_SINGLEShape.twl";
connectAttr "skinCluster25GroupId.id" "Joint_1_Object_30_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster25Set.mwc" "Joint_1_Object_30_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId50.id" "Joint_1_Object_30_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet25.mwc" "Joint_1_Object_30_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster25.og[0]" "Joint_1_Object_30_SINGLEShape.i";
connectAttr "tweak25.vl[0].vt[0]" "Joint_1_Object_30_SINGLEShape.twl";
connectAttr "skinCluster26GroupId.id" "Joint_1_Object_31_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster26Set.mwc" "Joint_1_Object_31_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId52.id" "Joint_1_Object_31_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet26.mwc" "Joint_1_Object_31_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster26.og[0]" "Joint_1_Object_31_SINGLEShape.i";
connectAttr "tweak26.vl[0].vt[0]" "Joint_1_Object_31_SINGLEShape.twl";
connectAttr "skinCluster27GroupId.id" "Joint_1_Object_32_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster27Set.mwc" "Joint_1_Object_32_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId54.id" "Joint_1_Object_32_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet27.mwc" "Joint_1_Object_32_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster27.og[0]" "Joint_1_Object_32_SINGLEShape.i";
connectAttr "tweak27.vl[0].vt[0]" "Joint_1_Object_32_SINGLEShape.twl";
connectAttr "skinCluster28GroupId.id" "Joint_1_Object_33_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster28Set.mwc" "Joint_1_Object_33_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId56.id" "Joint_1_Object_33_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet28.mwc" "Joint_1_Object_33_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster28.og[0]" "Joint_1_Object_33_SINGLEShape.i";
connectAttr "tweak28.vl[0].vt[0]" "Joint_1_Object_33_SINGLEShape.twl";
connectAttr "skinCluster29GroupId.id" "Joint_1_Object_34_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster29Set.mwc" "Joint_1_Object_34_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId58.id" "Joint_1_Object_34_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet29.mwc" "Joint_1_Object_34_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster29.og[0]" "Joint_1_Object_34_SINGLEShape.i";
connectAttr "tweak29.vl[0].vt[0]" "Joint_1_Object_34_SINGLEShape.twl";
connectAttr "skinCluster30GroupId.id" "Joint_1_Object_35_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster30Set.mwc" "Joint_1_Object_35_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId60.id" "Joint_1_Object_35_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet30.mwc" "Joint_1_Object_35_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster30.og[0]" "Joint_1_Object_35_SINGLEShape.i";
connectAttr "tweak30.vl[0].vt[0]" "Joint_1_Object_35_SINGLEShape.twl";
connectAttr "skinCluster31GroupId.id" "Joint_1_Object_36_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster31Set.mwc" "Joint_1_Object_36_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId62.id" "Joint_1_Object_36_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet31.mwc" "Joint_1_Object_36_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster31.og[0]" "Joint_1_Object_36_SINGLEShape.i";
connectAttr "tweak31.vl[0].vt[0]" "Joint_1_Object_36_SINGLEShape.twl";
connectAttr "skinCluster32GroupId.id" "Joint_1_Object_37_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster32Set.mwc" "Joint_1_Object_37_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId64.id" "Joint_1_Object_37_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet32.mwc" "Joint_1_Object_37_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster32.og[0]" "Joint_1_Object_37_SINGLEShape.i";
connectAttr "tweak32.vl[0].vt[0]" "Joint_1_Object_37_SINGLEShape.twl";
connectAttr "skinCluster33GroupId.id" "Joint_1_Object_38_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster33Set.mwc" "Joint_1_Object_38_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId66.id" "Joint_1_Object_38_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet33.mwc" "Joint_1_Object_38_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster33.og[0]" "Joint_1_Object_38_SINGLEShape.i";
connectAttr "tweak33.vl[0].vt[0]" "Joint_1_Object_38_SINGLEShape.twl";
connectAttr "skinCluster34GroupId.id" "Joint_1_Object_39_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster34Set.mwc" "Joint_1_Object_39_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId68.id" "Joint_1_Object_39_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet34.mwc" "Joint_1_Object_39_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster34.og[0]" "Joint_1_Object_39_SINGLEShape.i";
connectAttr "tweak34.vl[0].vt[0]" "Joint_1_Object_39_SINGLEShape.twl";
connectAttr "skinCluster36GroupId.id" "Joint_1_Object_40_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster36Set.mwc" "Joint_1_Object_40_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId72.id" "Joint_1_Object_40_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet36.mwc" "Joint_1_Object_40_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster36.og[0]" "Joint_1_Object_40_SINGLEShape.i";
connectAttr "tweak36.vl[0].vt[0]" "Joint_1_Object_40_SINGLEShape.twl";
connectAttr "skinCluster37GroupId.id" "Joint_1_Object_41_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster37Set.mwc" "Joint_1_Object_41_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId74.id" "Joint_1_Object_41_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet37.mwc" "Joint_1_Object_41_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster37.og[0]" "Joint_1_Object_41_SINGLEShape.i";
connectAttr "tweak37.vl[0].vt[0]" "Joint_1_Object_41_SINGLEShape.twl";
connectAttr "skinCluster38GroupId.id" "Joint_1_Object_42_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster38Set.mwc" "Joint_1_Object_42_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId76.id" "Joint_1_Object_42_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet38.mwc" "Joint_1_Object_42_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster38.og[0]" "Joint_1_Object_42_SINGLEShape.i";
connectAttr "tweak38.vl[0].vt[0]" "Joint_1_Object_42_SINGLEShape.twl";
connectAttr "skinCluster39GroupId.id" "Joint_1_Object_43_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster39Set.mwc" "Joint_1_Object_43_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId78.id" "Joint_1_Object_43_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet39.mwc" "Joint_1_Object_43_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster39.og[0]" "Joint_1_Object_43_SINGLEShape.i";
connectAttr "tweak39.vl[0].vt[0]" "Joint_1_Object_43_SINGLEShape.twl";
connectAttr "skinCluster40GroupId.id" "Joint_1_Object_44_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster40Set.mwc" "Joint_1_Object_44_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId80.id" "Joint_1_Object_44_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet40.mwc" "Joint_1_Object_44_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster40.og[0]" "Joint_1_Object_44_SINGLEShape.i";
connectAttr "tweak40.vl[0].vt[0]" "Joint_1_Object_44_SINGLEShape.twl";
connectAttr "skinCluster41GroupId.id" "Joint_1_Object_45_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster41Set.mwc" "Joint_1_Object_45_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId82.id" "Joint_1_Object_45_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet41.mwc" "Joint_1_Object_45_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster41.og[0]" "Joint_1_Object_45_SINGLEShape.i";
connectAttr "tweak41.vl[0].vt[0]" "Joint_1_Object_45_SINGLEShape.twl";
connectAttr "skinCluster42GroupId.id" "Joint_1_Object_46_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster42Set.mwc" "Joint_1_Object_46_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId84.id" "Joint_1_Object_46_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet42.mwc" "Joint_1_Object_46_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster42.og[0]" "Joint_1_Object_46_SINGLEShape.i";
connectAttr "tweak42.vl[0].vt[0]" "Joint_1_Object_46_SINGLEShape.twl";
connectAttr "skinCluster43GroupId.id" "Joint_1_Object_47_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster43Set.mwc" "Joint_1_Object_47_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId86.id" "Joint_1_Object_47_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet43.mwc" "Joint_1_Object_47_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster43.og[0]" "Joint_1_Object_47_SINGLEShape.i";
connectAttr "tweak43.vl[0].vt[0]" "Joint_1_Object_47_SINGLEShape.twl";
connectAttr "skinCluster44GroupId.id" "Joint_1_Object_48_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster44Set.mwc" "Joint_1_Object_48_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId88.id" "Joint_1_Object_48_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet44.mwc" "Joint_1_Object_48_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster44.og[0]" "Joint_1_Object_48_SINGLEShape.i";
connectAttr "tweak44.vl[0].vt[0]" "Joint_1_Object_48_SINGLEShape.twl";
connectAttr "skinCluster45GroupId.id" "Joint_1_Object_49_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster45Set.mwc" "Joint_1_Object_49_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId90.id" "Joint_1_Object_49_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet45.mwc" "Joint_1_Object_49_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster45.og[0]" "Joint_1_Object_49_SINGLEShape.i";
connectAttr "tweak45.vl[0].vt[0]" "Joint_1_Object_49_SINGLEShape.twl";
connectAttr "skinCluster47GroupId.id" "Joint_1_Object_50_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster47Set.mwc" "Joint_1_Object_50_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId94.id" "Joint_1_Object_50_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet47.mwc" "Joint_1_Object_50_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster47.og[0]" "Joint_1_Object_50_SINGLEShape.i";
connectAttr "tweak47.vl[0].vt[0]" "Joint_1_Object_50_SINGLEShape.twl";
connectAttr "skinCluster48GroupId.id" "Joint_1_Object_51_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster48Set.mwc" "Joint_1_Object_51_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId96.id" "Joint_1_Object_51_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet48.mwc" "Joint_1_Object_51_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster48.og[0]" "Joint_1_Object_51_SINGLEShape.i";
connectAttr "tweak48.vl[0].vt[0]" "Joint_1_Object_51_SINGLEShape.twl";
connectAttr "skinCluster49GroupId.id" "Joint_1_Object_52_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster49Set.mwc" "Joint_1_Object_52_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId98.id" "Joint_1_Object_52_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet49.mwc" "Joint_1_Object_52_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster49.og[0]" "Joint_1_Object_52_SINGLEShape.i";
connectAttr "tweak49.vl[0].vt[0]" "Joint_1_Object_52_SINGLEShape.twl";
connectAttr "skinCluster50GroupId.id" "Joint_1_Object_53_SINGLEShape.iog.og[0].gid"
		;
connectAttr "skinCluster50Set.mwc" "Joint_1_Object_53_SINGLEShape.iog.og[0].gco"
		;
connectAttr "groupId100.id" "Joint_1_Object_53_SINGLEShape.iog.og[1].gid";
connectAttr "tweakSet50.mwc" "Joint_1_Object_53_SINGLEShape.iog.og[1].gco";
connectAttr "skinCluster50.og[0]" "Joint_1_Object_53_SINGLEShape.i";
connectAttr "tweak50.vl[0].vt[0]" "Joint_1_Object_53_SINGLEShape.twl";
relationship "link" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_0_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_1_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_2_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_3_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_4_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_5_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_6_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_7_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_8_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_9_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_10_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_11_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_12_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_13_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_14_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_15_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_16_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_17_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_18_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_19_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_20_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_21_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_22_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_23_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_24_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_25_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_26_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_27_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_28_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_29_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_30_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_31_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_32_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_33_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_34_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_35_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_36_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_37_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_38_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_39_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_40_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_41_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_42_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_43_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_44_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_45_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_46_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_47_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_48_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_49_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_50_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_51_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_52_SINGLESG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "Joint_1_Object_53_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_0_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_1_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_2_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_3_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_4_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_5_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_6_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_7_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_8_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_9_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_10_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_11_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_12_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_13_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_14_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_15_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_16_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_17_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_18_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_19_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_20_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_21_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_22_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_23_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_24_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_25_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_26_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_27_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_28_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_29_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_30_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_31_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_32_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_33_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_34_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_35_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_36_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_37_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_38_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_39_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_40_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_41_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_42_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_43_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_44_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_45_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_46_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_47_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_48_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_49_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_50_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_51_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_52_SINGLESG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "Joint_1_Object_53_SINGLESG.message" ":defaultLightSet.message";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr "Image.oc" "Joint_1_Object_0_Material_0.c";
connectAttr "Joint_1_Object_0_Material_0.oc" "Joint_1_Object_0_SINGLESG.ss";
connectAttr "Joint_1_Object_0_SINGLEShape.iog" "Joint_1_Object_0_SINGLESG.dsm" -na
		;
connectAttr "Joint_1_Object_0_SINGLESG.msg" "materialInfo1.sg";
connectAttr "Joint_1_Object_0_Material_0.msg" "materialInfo1.m";
connectAttr "Image.msg" "materialInfo1.t" -na;
connectAttr "place2dTexture1.o" "Image.uv";
connectAttr "place2dTexture1.ofu" "Image.ofu";
connectAttr "place2dTexture1.ofv" "Image.ofv";
connectAttr "place2dTexture1.rf" "Image.rf";
connectAttr "place2dTexture1.reu" "Image.reu";
connectAttr "place2dTexture1.rev" "Image.rev";
connectAttr "place2dTexture1.vt1" "Image.vt1";
connectAttr "place2dTexture1.vt2" "Image.vt2";
connectAttr "place2dTexture1.vt3" "Image.vt3";
connectAttr "place2dTexture1.vc1" "Image.vc1";
connectAttr "place2dTexture1.ofs" "Image.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image.ws";
connectAttr "Image1.oc" "Joint_1_Object_1_Material_1.c";
connectAttr "Joint_1_Object_1_Material_1.oc" "Joint_1_Object_1_SINGLESG.ss";
connectAttr "Joint_1_Object_1_SINGLEShape.iog" "Joint_1_Object_1_SINGLESG.dsm" -na
		;
connectAttr "Joint_1_Object_1_SINGLESG.msg" "materialInfo2.sg";
connectAttr "Joint_1_Object_1_Material_1.msg" "materialInfo2.m";
connectAttr "Image1.msg" "materialInfo2.t" -na;
connectAttr "place2dTexture2.o" "Image1.uv";
connectAttr "place2dTexture2.ofu" "Image1.ofu";
connectAttr "place2dTexture2.ofv" "Image1.ofv";
connectAttr "place2dTexture2.rf" "Image1.rf";
connectAttr "place2dTexture2.reu" "Image1.reu";
connectAttr "place2dTexture2.rev" "Image1.rev";
connectAttr "place2dTexture2.vt1" "Image1.vt1";
connectAttr "place2dTexture2.vt2" "Image1.vt2";
connectAttr "place2dTexture2.vt3" "Image1.vt3";
connectAttr "place2dTexture2.vc1" "Image1.vc1";
connectAttr "place2dTexture2.ofs" "Image1.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image1.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image1.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image1.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image1.ws";
connectAttr "Image2.oc" "Joint_1_Object_2_Material_2.c";
connectAttr "Joint_1_Object_2_Material_2.oc" "Joint_1_Object_2_SINGLESG.ss";
connectAttr "Joint_1_Object_2_SINGLEShape.iog" "Joint_1_Object_2_SINGLESG.dsm" -na
		;
connectAttr "Joint_1_Object_2_SINGLESG.msg" "materialInfo3.sg";
connectAttr "Joint_1_Object_2_Material_2.msg" "materialInfo3.m";
connectAttr "Image2.msg" "materialInfo3.t" -na;
connectAttr "place2dTexture3.o" "Image2.uv";
connectAttr "place2dTexture3.ofu" "Image2.ofu";
connectAttr "place2dTexture3.ofv" "Image2.ofv";
connectAttr "place2dTexture3.rf" "Image2.rf";
connectAttr "place2dTexture3.reu" "Image2.reu";
connectAttr "place2dTexture3.rev" "Image2.rev";
connectAttr "place2dTexture3.vt1" "Image2.vt1";
connectAttr "place2dTexture3.vt2" "Image2.vt2";
connectAttr "place2dTexture3.vt3" "Image2.vt3";
connectAttr "place2dTexture3.vc1" "Image2.vc1";
connectAttr "place2dTexture3.ofs" "Image2.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image2.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image2.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image2.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image2.ws";
connectAttr "Image3.oc" "Joint_1_Object_3_Material_3.c";
connectAttr "Joint_1_Object_3_Material_3.oc" "Joint_1_Object_3_SINGLESG.ss";
connectAttr "Joint_1_Object_3_SINGLEShape.iog" "Joint_1_Object_3_SINGLESG.dsm" -na
		;
connectAttr "Joint_1_Object_3_SINGLESG.msg" "materialInfo4.sg";
connectAttr "Joint_1_Object_3_Material_3.msg" "materialInfo4.m";
connectAttr "Image3.msg" "materialInfo4.t" -na;
connectAttr "place2dTexture4.o" "Image3.uv";
connectAttr "place2dTexture4.ofu" "Image3.ofu";
connectAttr "place2dTexture4.ofv" "Image3.ofv";
connectAttr "place2dTexture4.rf" "Image3.rf";
connectAttr "place2dTexture4.reu" "Image3.reu";
connectAttr "place2dTexture4.rev" "Image3.rev";
connectAttr "place2dTexture4.vt1" "Image3.vt1";
connectAttr "place2dTexture4.vt2" "Image3.vt2";
connectAttr "place2dTexture4.vt3" "Image3.vt3";
connectAttr "place2dTexture4.vc1" "Image3.vc1";
connectAttr "place2dTexture4.ofs" "Image3.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image3.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image3.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image3.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image3.ws";
connectAttr "Image4.oc" "Joint_1_Object_4_Material_4.c";
connectAttr "Joint_1_Object_4_Material_4.oc" "Joint_1_Object_4_SINGLESG.ss";
connectAttr "Joint_1_Object_4_SINGLEShape.iog" "Joint_1_Object_4_SINGLESG.dsm" -na
		;
connectAttr "Joint_1_Object_4_SINGLESG.msg" "materialInfo5.sg";
connectAttr "Joint_1_Object_4_Material_4.msg" "materialInfo5.m";
connectAttr "Image4.msg" "materialInfo5.t" -na;
connectAttr "place2dTexture5.o" "Image4.uv";
connectAttr "place2dTexture5.ofu" "Image4.ofu";
connectAttr "place2dTexture5.ofv" "Image4.ofv";
connectAttr "place2dTexture5.rf" "Image4.rf";
connectAttr "place2dTexture5.reu" "Image4.reu";
connectAttr "place2dTexture5.rev" "Image4.rev";
connectAttr "place2dTexture5.vt1" "Image4.vt1";
connectAttr "place2dTexture5.vt2" "Image4.vt2";
connectAttr "place2dTexture5.vt3" "Image4.vt3";
connectAttr "place2dTexture5.vc1" "Image4.vc1";
connectAttr "place2dTexture5.ofs" "Image4.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image4.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image4.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image4.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image4.ws";
connectAttr "Image5.oc" "Joint_1_Object_5_Material_5.c";
connectAttr "Joint_1_Object_5_Material_5.oc" "Joint_1_Object_5_SINGLESG.ss";
connectAttr "Joint_1_Object_5_SINGLEShape.iog" "Joint_1_Object_5_SINGLESG.dsm" -na
		;
connectAttr "Joint_1_Object_5_SINGLESG.msg" "materialInfo6.sg";
connectAttr "Joint_1_Object_5_Material_5.msg" "materialInfo6.m";
connectAttr "Image5.msg" "materialInfo6.t" -na;
connectAttr "place2dTexture6.o" "Image5.uv";
connectAttr "place2dTexture6.ofu" "Image5.ofu";
connectAttr "place2dTexture6.ofv" "Image5.ofv";
connectAttr "place2dTexture6.rf" "Image5.rf";
connectAttr "place2dTexture6.reu" "Image5.reu";
connectAttr "place2dTexture6.rev" "Image5.rev";
connectAttr "place2dTexture6.vt1" "Image5.vt1";
connectAttr "place2dTexture6.vt2" "Image5.vt2";
connectAttr "place2dTexture6.vt3" "Image5.vt3";
connectAttr "place2dTexture6.vc1" "Image5.vc1";
connectAttr "place2dTexture6.ofs" "Image5.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image5.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image5.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image5.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image5.ws";
connectAttr "Image6.oc" "Joint_1_Object_6_Material_6.c";
connectAttr "Joint_1_Object_6_Material_6.oc" "Joint_1_Object_6_SINGLESG.ss";
connectAttr "Joint_1_Object_6_SINGLEShape.iog" "Joint_1_Object_6_SINGLESG.dsm" -na
		;
connectAttr "Joint_1_Object_6_SINGLESG.msg" "materialInfo7.sg";
connectAttr "Joint_1_Object_6_Material_6.msg" "materialInfo7.m";
connectAttr "Image6.msg" "materialInfo7.t" -na;
connectAttr "place2dTexture7.o" "Image6.uv";
connectAttr "place2dTexture7.ofu" "Image6.ofu";
connectAttr "place2dTexture7.ofv" "Image6.ofv";
connectAttr "place2dTexture7.rf" "Image6.rf";
connectAttr "place2dTexture7.reu" "Image6.reu";
connectAttr "place2dTexture7.rev" "Image6.rev";
connectAttr "place2dTexture7.vt1" "Image6.vt1";
connectAttr "place2dTexture7.vt2" "Image6.vt2";
connectAttr "place2dTexture7.vt3" "Image6.vt3";
connectAttr "place2dTexture7.vc1" "Image6.vc1";
connectAttr "place2dTexture7.ofs" "Image6.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image6.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image6.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image6.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image6.ws";
connectAttr "Image7.oc" "Joint_1_Object_7_Material_7.c";
connectAttr "Joint_1_Object_7_Material_7.oc" "Joint_1_Object_7_SINGLESG.ss";
connectAttr "Joint_1_Object_7_SINGLEShape.iog" "Joint_1_Object_7_SINGLESG.dsm" -na
		;
connectAttr "Joint_1_Object_7_SINGLESG.msg" "materialInfo8.sg";
connectAttr "Joint_1_Object_7_Material_7.msg" "materialInfo8.m";
connectAttr "Image7.msg" "materialInfo8.t" -na;
connectAttr "place2dTexture8.o" "Image7.uv";
connectAttr "place2dTexture8.ofu" "Image7.ofu";
connectAttr "place2dTexture8.ofv" "Image7.ofv";
connectAttr "place2dTexture8.rf" "Image7.rf";
connectAttr "place2dTexture8.reu" "Image7.reu";
connectAttr "place2dTexture8.rev" "Image7.rev";
connectAttr "place2dTexture8.vt1" "Image7.vt1";
connectAttr "place2dTexture8.vt2" "Image7.vt2";
connectAttr "place2dTexture8.vt3" "Image7.vt3";
connectAttr "place2dTexture8.vc1" "Image7.vc1";
connectAttr "place2dTexture8.ofs" "Image7.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image7.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image7.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image7.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image7.ws";
connectAttr "Image8.oc" "Joint_1_Object_8_Material_8.c";
connectAttr "Joint_1_Object_8_Material_8.oc" "Joint_1_Object_8_SINGLESG.ss";
connectAttr "Joint_1_Object_8_SINGLEShape.iog" "Joint_1_Object_8_SINGLESG.dsm" -na
		;
connectAttr "Joint_1_Object_8_SINGLESG.msg" "materialInfo9.sg";
connectAttr "Joint_1_Object_8_Material_8.msg" "materialInfo9.m";
connectAttr "Image8.msg" "materialInfo9.t" -na;
connectAttr "place2dTexture9.o" "Image8.uv";
connectAttr "place2dTexture9.ofu" "Image8.ofu";
connectAttr "place2dTexture9.ofv" "Image8.ofv";
connectAttr "place2dTexture9.rf" "Image8.rf";
connectAttr "place2dTexture9.reu" "Image8.reu";
connectAttr "place2dTexture9.rev" "Image8.rev";
connectAttr "place2dTexture9.vt1" "Image8.vt1";
connectAttr "place2dTexture9.vt2" "Image8.vt2";
connectAttr "place2dTexture9.vt3" "Image8.vt3";
connectAttr "place2dTexture9.vc1" "Image8.vc1";
connectAttr "place2dTexture9.ofs" "Image8.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image8.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image8.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image8.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image8.ws";
connectAttr "Image9.oc" "Joint_1_Object_9_Material_9.c";
connectAttr "Joint_1_Object_9_Material_9.oc" "Joint_1_Object_9_SINGLESG.ss";
connectAttr "Joint_1_Object_9_SINGLEShape.iog" "Joint_1_Object_9_SINGLESG.dsm" -na
		;
connectAttr "Joint_1_Object_9_SINGLESG.msg" "materialInfo10.sg";
connectAttr "Joint_1_Object_9_Material_9.msg" "materialInfo10.m";
connectAttr "Image9.msg" "materialInfo10.t" -na;
connectAttr "place2dTexture10.o" "Image9.uv";
connectAttr "place2dTexture10.ofu" "Image9.ofu";
connectAttr "place2dTexture10.ofv" "Image9.ofv";
connectAttr "place2dTexture10.rf" "Image9.rf";
connectAttr "place2dTexture10.reu" "Image9.reu";
connectAttr "place2dTexture10.rev" "Image9.rev";
connectAttr "place2dTexture10.vt1" "Image9.vt1";
connectAttr "place2dTexture10.vt2" "Image9.vt2";
connectAttr "place2dTexture10.vt3" "Image9.vt3";
connectAttr "place2dTexture10.vc1" "Image9.vc1";
connectAttr "place2dTexture10.ofs" "Image9.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image9.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image9.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image9.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image9.ws";
connectAttr "Image10.oc" "Joint_1_Object_10_Material_10.c";
connectAttr "Joint_1_Object_10_Material_10.oc" "Joint_1_Object_10_SINGLESG.ss";
connectAttr "Joint_1_Object_10_SINGLEShape.iog" "Joint_1_Object_10_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_10_SINGLESG.msg" "materialInfo11.sg";
connectAttr "Joint_1_Object_10_Material_10.msg" "materialInfo11.m";
connectAttr "Image10.msg" "materialInfo11.t" -na;
connectAttr "place2dTexture11.o" "Image10.uv";
connectAttr "place2dTexture11.ofu" "Image10.ofu";
connectAttr "place2dTexture11.ofv" "Image10.ofv";
connectAttr "place2dTexture11.rf" "Image10.rf";
connectAttr "place2dTexture11.reu" "Image10.reu";
connectAttr "place2dTexture11.rev" "Image10.rev";
connectAttr "place2dTexture11.vt1" "Image10.vt1";
connectAttr "place2dTexture11.vt2" "Image10.vt2";
connectAttr "place2dTexture11.vt3" "Image10.vt3";
connectAttr "place2dTexture11.vc1" "Image10.vc1";
connectAttr "place2dTexture11.ofs" "Image10.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image10.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image10.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image10.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image10.ws";
connectAttr "Image11.oc" "Joint_1_Object_11_Material_11.c";
connectAttr "Joint_1_Object_11_Material_11.oc" "Joint_1_Object_11_SINGLESG.ss";
connectAttr "Joint_1_Object_11_SINGLEShape.iog" "Joint_1_Object_11_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_11_SINGLESG.msg" "materialInfo12.sg";
connectAttr "Joint_1_Object_11_Material_11.msg" "materialInfo12.m";
connectAttr "Image11.msg" "materialInfo12.t" -na;
connectAttr "place2dTexture12.o" "Image11.uv";
connectAttr "place2dTexture12.ofu" "Image11.ofu";
connectAttr "place2dTexture12.ofv" "Image11.ofv";
connectAttr "place2dTexture12.rf" "Image11.rf";
connectAttr "place2dTexture12.reu" "Image11.reu";
connectAttr "place2dTexture12.rev" "Image11.rev";
connectAttr "place2dTexture12.vt1" "Image11.vt1";
connectAttr "place2dTexture12.vt2" "Image11.vt2";
connectAttr "place2dTexture12.vt3" "Image11.vt3";
connectAttr "place2dTexture12.vc1" "Image11.vc1";
connectAttr "place2dTexture12.ofs" "Image11.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image11.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image11.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image11.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image11.ws";
connectAttr "Image12.oc" "Joint_1_Object_12_Material_12.c";
connectAttr "Joint_1_Object_12_Material_12.oc" "Joint_1_Object_12_SINGLESG.ss";
connectAttr "Joint_1_Object_12_SINGLEShape.iog" "Joint_1_Object_12_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_12_SINGLESG.msg" "materialInfo13.sg";
connectAttr "Joint_1_Object_12_Material_12.msg" "materialInfo13.m";
connectAttr "Image12.msg" "materialInfo13.t" -na;
connectAttr "place2dTexture13.o" "Image12.uv";
connectAttr "place2dTexture13.ofu" "Image12.ofu";
connectAttr "place2dTexture13.ofv" "Image12.ofv";
connectAttr "place2dTexture13.rf" "Image12.rf";
connectAttr "place2dTexture13.reu" "Image12.reu";
connectAttr "place2dTexture13.rev" "Image12.rev";
connectAttr "place2dTexture13.vt1" "Image12.vt1";
connectAttr "place2dTexture13.vt2" "Image12.vt2";
connectAttr "place2dTexture13.vt3" "Image12.vt3";
connectAttr "place2dTexture13.vc1" "Image12.vc1";
connectAttr "place2dTexture13.ofs" "Image12.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image12.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image12.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image12.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image12.ws";
connectAttr "Image13.oc" "Joint_1_Object_13_Material_13.c";
connectAttr "Joint_1_Object_13_Material_13.oc" "Joint_1_Object_13_SINGLESG.ss";
connectAttr "Joint_1_Object_13_SINGLEShape.iog" "Joint_1_Object_13_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_13_SINGLESG.msg" "materialInfo14.sg";
connectAttr "Joint_1_Object_13_Material_13.msg" "materialInfo14.m";
connectAttr "Image13.msg" "materialInfo14.t" -na;
connectAttr "place2dTexture14.o" "Image13.uv";
connectAttr "place2dTexture14.ofu" "Image13.ofu";
connectAttr "place2dTexture14.ofv" "Image13.ofv";
connectAttr "place2dTexture14.rf" "Image13.rf";
connectAttr "place2dTexture14.reu" "Image13.reu";
connectAttr "place2dTexture14.rev" "Image13.rev";
connectAttr "place2dTexture14.vt1" "Image13.vt1";
connectAttr "place2dTexture14.vt2" "Image13.vt2";
connectAttr "place2dTexture14.vt3" "Image13.vt3";
connectAttr "place2dTexture14.vc1" "Image13.vc1";
connectAttr "place2dTexture14.ofs" "Image13.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image13.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image13.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image13.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image13.ws";
connectAttr "Image14.oc" "Joint_1_Object_14_Material_14.c";
connectAttr "Joint_1_Object_14_Material_14.oc" "Joint_1_Object_14_SINGLESG.ss";
connectAttr "Joint_1_Object_14_SINGLEShape.iog" "Joint_1_Object_14_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_14_SINGLESG.msg" "materialInfo15.sg";
connectAttr "Joint_1_Object_14_Material_14.msg" "materialInfo15.m";
connectAttr "Image14.msg" "materialInfo15.t" -na;
connectAttr "place2dTexture15.o" "Image14.uv";
connectAttr "place2dTexture15.ofu" "Image14.ofu";
connectAttr "place2dTexture15.ofv" "Image14.ofv";
connectAttr "place2dTexture15.rf" "Image14.rf";
connectAttr "place2dTexture15.reu" "Image14.reu";
connectAttr "place2dTexture15.rev" "Image14.rev";
connectAttr "place2dTexture15.vt1" "Image14.vt1";
connectAttr "place2dTexture15.vt2" "Image14.vt2";
connectAttr "place2dTexture15.vt3" "Image14.vt3";
connectAttr "place2dTexture15.vc1" "Image14.vc1";
connectAttr "place2dTexture15.ofs" "Image14.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image14.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image14.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image14.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image14.ws";
connectAttr "Image15.oc" "Joint_1_Object_15_Material_15.c";
connectAttr "Joint_1_Object_15_Material_15.oc" "Joint_1_Object_15_SINGLESG.ss";
connectAttr "Joint_1_Object_15_SINGLEShape.iog" "Joint_1_Object_15_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_15_SINGLESG.msg" "materialInfo16.sg";
connectAttr "Joint_1_Object_15_Material_15.msg" "materialInfo16.m";
connectAttr "Image15.msg" "materialInfo16.t" -na;
connectAttr "place2dTexture16.o" "Image15.uv";
connectAttr "place2dTexture16.ofu" "Image15.ofu";
connectAttr "place2dTexture16.ofv" "Image15.ofv";
connectAttr "place2dTexture16.rf" "Image15.rf";
connectAttr "place2dTexture16.reu" "Image15.reu";
connectAttr "place2dTexture16.rev" "Image15.rev";
connectAttr "place2dTexture16.vt1" "Image15.vt1";
connectAttr "place2dTexture16.vt2" "Image15.vt2";
connectAttr "place2dTexture16.vt3" "Image15.vt3";
connectAttr "place2dTexture16.vc1" "Image15.vc1";
connectAttr "place2dTexture16.ofs" "Image15.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image15.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image15.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image15.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image15.ws";
connectAttr "Image16.oc" "Joint_1_Object_16_Material_16.c";
connectAttr "Joint_1_Object_16_Material_16.oc" "Joint_1_Object_16_SINGLESG.ss";
connectAttr "Joint_1_Object_16_SINGLEShape.iog" "Joint_1_Object_16_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_16_SINGLESG.msg" "materialInfo17.sg";
connectAttr "Joint_1_Object_16_Material_16.msg" "materialInfo17.m";
connectAttr "Image16.msg" "materialInfo17.t" -na;
connectAttr "place2dTexture17.o" "Image16.uv";
connectAttr "place2dTexture17.ofu" "Image16.ofu";
connectAttr "place2dTexture17.ofv" "Image16.ofv";
connectAttr "place2dTexture17.rf" "Image16.rf";
connectAttr "place2dTexture17.reu" "Image16.reu";
connectAttr "place2dTexture17.rev" "Image16.rev";
connectAttr "place2dTexture17.vt1" "Image16.vt1";
connectAttr "place2dTexture17.vt2" "Image16.vt2";
connectAttr "place2dTexture17.vt3" "Image16.vt3";
connectAttr "place2dTexture17.vc1" "Image16.vc1";
connectAttr "place2dTexture17.ofs" "Image16.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image16.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image16.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image16.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image16.ws";
connectAttr "Image17.oc" "Joint_1_Object_17_Material_17.c";
connectAttr "Joint_1_Object_17_Material_17.oc" "Joint_1_Object_17_SINGLESG.ss";
connectAttr "Joint_1_Object_17_SINGLEShape.iog" "Joint_1_Object_17_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_17_SINGLESG.msg" "materialInfo18.sg";
connectAttr "Joint_1_Object_17_Material_17.msg" "materialInfo18.m";
connectAttr "Image17.msg" "materialInfo18.t" -na;
connectAttr "place2dTexture18.o" "Image17.uv";
connectAttr "place2dTexture18.ofu" "Image17.ofu";
connectAttr "place2dTexture18.ofv" "Image17.ofv";
connectAttr "place2dTexture18.rf" "Image17.rf";
connectAttr "place2dTexture18.reu" "Image17.reu";
connectAttr "place2dTexture18.rev" "Image17.rev";
connectAttr "place2dTexture18.vt1" "Image17.vt1";
connectAttr "place2dTexture18.vt2" "Image17.vt2";
connectAttr "place2dTexture18.vt3" "Image17.vt3";
connectAttr "place2dTexture18.vc1" "Image17.vc1";
connectAttr "place2dTexture18.ofs" "Image17.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image17.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image17.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image17.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image17.ws";
connectAttr "Image18.oc" "Joint_1_Object_18_Material_18.c";
connectAttr "Joint_1_Object_18_Material_18.oc" "Joint_1_Object_18_SINGLESG.ss";
connectAttr "Joint_1_Object_18_SINGLEShape.iog" "Joint_1_Object_18_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_18_SINGLESG.msg" "materialInfo19.sg";
connectAttr "Joint_1_Object_18_Material_18.msg" "materialInfo19.m";
connectAttr "Image18.msg" "materialInfo19.t" -na;
connectAttr "place2dTexture19.o" "Image18.uv";
connectAttr "place2dTexture19.ofu" "Image18.ofu";
connectAttr "place2dTexture19.ofv" "Image18.ofv";
connectAttr "place2dTexture19.rf" "Image18.rf";
connectAttr "place2dTexture19.reu" "Image18.reu";
connectAttr "place2dTexture19.rev" "Image18.rev";
connectAttr "place2dTexture19.vt1" "Image18.vt1";
connectAttr "place2dTexture19.vt2" "Image18.vt2";
connectAttr "place2dTexture19.vt3" "Image18.vt3";
connectAttr "place2dTexture19.vc1" "Image18.vc1";
connectAttr "place2dTexture19.ofs" "Image18.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image18.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image18.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image18.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image18.ws";
connectAttr "Image19.oc" "Joint_1_Object_19_Material_19.c";
connectAttr "Joint_1_Object_19_Material_19.oc" "Joint_1_Object_19_SINGLESG.ss";
connectAttr "Joint_1_Object_19_SINGLEShape.iog" "Joint_1_Object_19_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_19_SINGLESG.msg" "materialInfo20.sg";
connectAttr "Joint_1_Object_19_Material_19.msg" "materialInfo20.m";
connectAttr "Image19.msg" "materialInfo20.t" -na;
connectAttr "place2dTexture20.o" "Image19.uv";
connectAttr "place2dTexture20.ofu" "Image19.ofu";
connectAttr "place2dTexture20.ofv" "Image19.ofv";
connectAttr "place2dTexture20.rf" "Image19.rf";
connectAttr "place2dTexture20.reu" "Image19.reu";
connectAttr "place2dTexture20.rev" "Image19.rev";
connectAttr "place2dTexture20.vt1" "Image19.vt1";
connectAttr "place2dTexture20.vt2" "Image19.vt2";
connectAttr "place2dTexture20.vt3" "Image19.vt3";
connectAttr "place2dTexture20.vc1" "Image19.vc1";
connectAttr "place2dTexture20.ofs" "Image19.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image19.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image19.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image19.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image19.ws";
connectAttr "Image20.oc" "Joint_1_Object_20_Material_20.c";
connectAttr "Joint_1_Object_20_Material_20.oc" "Joint_1_Object_20_SINGLESG.ss";
connectAttr "Joint_1_Object_20_SINGLEShape.iog" "Joint_1_Object_20_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_20_SINGLESG.msg" "materialInfo21.sg";
connectAttr "Joint_1_Object_20_Material_20.msg" "materialInfo21.m";
connectAttr "Image20.msg" "materialInfo21.t" -na;
connectAttr "place2dTexture21.o" "Image20.uv";
connectAttr "place2dTexture21.ofu" "Image20.ofu";
connectAttr "place2dTexture21.ofv" "Image20.ofv";
connectAttr "place2dTexture21.rf" "Image20.rf";
connectAttr "place2dTexture21.reu" "Image20.reu";
connectAttr "place2dTexture21.rev" "Image20.rev";
connectAttr "place2dTexture21.vt1" "Image20.vt1";
connectAttr "place2dTexture21.vt2" "Image20.vt2";
connectAttr "place2dTexture21.vt3" "Image20.vt3";
connectAttr "place2dTexture21.vc1" "Image20.vc1";
connectAttr "place2dTexture21.ofs" "Image20.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image20.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image20.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image20.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image20.ws";
connectAttr "Image21.oc" "Joint_1_Object_21_Material_21.c";
connectAttr "Joint_1_Object_21_Material_21.oc" "Joint_1_Object_21_SINGLESG.ss";
connectAttr "Joint_1_Object_21_SINGLEShape.iog" "Joint_1_Object_21_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_21_SINGLESG.msg" "materialInfo22.sg";
connectAttr "Joint_1_Object_21_Material_21.msg" "materialInfo22.m";
connectAttr "Image21.msg" "materialInfo22.t" -na;
connectAttr "place2dTexture22.o" "Image21.uv";
connectAttr "place2dTexture22.ofu" "Image21.ofu";
connectAttr "place2dTexture22.ofv" "Image21.ofv";
connectAttr "place2dTexture22.rf" "Image21.rf";
connectAttr "place2dTexture22.reu" "Image21.reu";
connectAttr "place2dTexture22.rev" "Image21.rev";
connectAttr "place2dTexture22.vt1" "Image21.vt1";
connectAttr "place2dTexture22.vt2" "Image21.vt2";
connectAttr "place2dTexture22.vt3" "Image21.vt3";
connectAttr "place2dTexture22.vc1" "Image21.vc1";
connectAttr "place2dTexture22.ofs" "Image21.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image21.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image21.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image21.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image21.ws";
connectAttr "Image22.oc" "Joint_1_Object_22_Material_22.c";
connectAttr "Joint_1_Object_22_Material_22.oc" "Joint_1_Object_22_SINGLESG.ss";
connectAttr "Joint_1_Object_22_SINGLEShape.iog" "Joint_1_Object_22_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_22_SINGLESG.msg" "materialInfo23.sg";
connectAttr "Joint_1_Object_22_Material_22.msg" "materialInfo23.m";
connectAttr "Image22.msg" "materialInfo23.t" -na;
connectAttr "place2dTexture23.o" "Image22.uv";
connectAttr "place2dTexture23.ofu" "Image22.ofu";
connectAttr "place2dTexture23.ofv" "Image22.ofv";
connectAttr "place2dTexture23.rf" "Image22.rf";
connectAttr "place2dTexture23.reu" "Image22.reu";
connectAttr "place2dTexture23.rev" "Image22.rev";
connectAttr "place2dTexture23.vt1" "Image22.vt1";
connectAttr "place2dTexture23.vt2" "Image22.vt2";
connectAttr "place2dTexture23.vt3" "Image22.vt3";
connectAttr "place2dTexture23.vc1" "Image22.vc1";
connectAttr "place2dTexture23.ofs" "Image22.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image22.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image22.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image22.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image22.ws";
connectAttr "Image23.oc" "Joint_1_Object_23_Material_23.c";
connectAttr "Joint_1_Object_23_Material_23.oc" "Joint_1_Object_23_SINGLESG.ss";
connectAttr "Joint_1_Object_23_SINGLEShape.iog" "Joint_1_Object_23_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_23_SINGLESG.msg" "materialInfo24.sg";
connectAttr "Joint_1_Object_23_Material_23.msg" "materialInfo24.m";
connectAttr "Image23.msg" "materialInfo24.t" -na;
connectAttr "place2dTexture24.o" "Image23.uv";
connectAttr "place2dTexture24.ofu" "Image23.ofu";
connectAttr "place2dTexture24.ofv" "Image23.ofv";
connectAttr "place2dTexture24.rf" "Image23.rf";
connectAttr "place2dTexture24.reu" "Image23.reu";
connectAttr "place2dTexture24.rev" "Image23.rev";
connectAttr "place2dTexture24.vt1" "Image23.vt1";
connectAttr "place2dTexture24.vt2" "Image23.vt2";
connectAttr "place2dTexture24.vt3" "Image23.vt3";
connectAttr "place2dTexture24.vc1" "Image23.vc1";
connectAttr "place2dTexture24.ofs" "Image23.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image23.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image23.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image23.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image23.ws";
connectAttr "Image24.oc" "Joint_1_Object_24_Material_24.c";
connectAttr "Joint_1_Object_24_Material_24.oc" "Joint_1_Object_24_SINGLESG.ss";
connectAttr "Joint_1_Object_24_SINGLEShape.iog" "Joint_1_Object_24_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_24_SINGLESG.msg" "materialInfo25.sg";
connectAttr "Joint_1_Object_24_Material_24.msg" "materialInfo25.m";
connectAttr "Image24.msg" "materialInfo25.t" -na;
connectAttr "place2dTexture25.o" "Image24.uv";
connectAttr "place2dTexture25.ofu" "Image24.ofu";
connectAttr "place2dTexture25.ofv" "Image24.ofv";
connectAttr "place2dTexture25.rf" "Image24.rf";
connectAttr "place2dTexture25.reu" "Image24.reu";
connectAttr "place2dTexture25.rev" "Image24.rev";
connectAttr "place2dTexture25.vt1" "Image24.vt1";
connectAttr "place2dTexture25.vt2" "Image24.vt2";
connectAttr "place2dTexture25.vt3" "Image24.vt3";
connectAttr "place2dTexture25.vc1" "Image24.vc1";
connectAttr "place2dTexture25.ofs" "Image24.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image24.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image24.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image24.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image24.ws";
connectAttr "Image25.oc" "Joint_1_Object_25_Material_25.c";
connectAttr "Joint_1_Object_25_Material_25.oc" "Joint_1_Object_25_SINGLESG.ss";
connectAttr "Joint_1_Object_25_SINGLEShape.iog" "Joint_1_Object_25_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_25_SINGLESG.msg" "materialInfo26.sg";
connectAttr "Joint_1_Object_25_Material_25.msg" "materialInfo26.m";
connectAttr "Image25.msg" "materialInfo26.t" -na;
connectAttr "place2dTexture26.o" "Image25.uv";
connectAttr "place2dTexture26.ofu" "Image25.ofu";
connectAttr "place2dTexture26.ofv" "Image25.ofv";
connectAttr "place2dTexture26.rf" "Image25.rf";
connectAttr "place2dTexture26.reu" "Image25.reu";
connectAttr "place2dTexture26.rev" "Image25.rev";
connectAttr "place2dTexture26.vt1" "Image25.vt1";
connectAttr "place2dTexture26.vt2" "Image25.vt2";
connectAttr "place2dTexture26.vt3" "Image25.vt3";
connectAttr "place2dTexture26.vc1" "Image25.vc1";
connectAttr "place2dTexture26.ofs" "Image25.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image25.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image25.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image25.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image25.ws";
connectAttr "Image26.oc" "Joint_1_Object_26_Material_26.c";
connectAttr "Joint_1_Object_26_Material_26.oc" "Joint_1_Object_26_SINGLESG.ss";
connectAttr "Joint_1_Object_26_SINGLEShape.iog" "Joint_1_Object_26_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_26_SINGLESG.msg" "materialInfo27.sg";
connectAttr "Joint_1_Object_26_Material_26.msg" "materialInfo27.m";
connectAttr "Image26.msg" "materialInfo27.t" -na;
connectAttr "place2dTexture27.o" "Image26.uv";
connectAttr "place2dTexture27.ofu" "Image26.ofu";
connectAttr "place2dTexture27.ofv" "Image26.ofv";
connectAttr "place2dTexture27.rf" "Image26.rf";
connectAttr "place2dTexture27.reu" "Image26.reu";
connectAttr "place2dTexture27.rev" "Image26.rev";
connectAttr "place2dTexture27.vt1" "Image26.vt1";
connectAttr "place2dTexture27.vt2" "Image26.vt2";
connectAttr "place2dTexture27.vt3" "Image26.vt3";
connectAttr "place2dTexture27.vc1" "Image26.vc1";
connectAttr "place2dTexture27.ofs" "Image26.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image26.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image26.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image26.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image26.ws";
connectAttr "Image27.oc" "Joint_1_Object_27_Material_27.c";
connectAttr "Joint_1_Object_27_Material_27.oc" "Joint_1_Object_27_SINGLESG.ss";
connectAttr "Joint_1_Object_27_SINGLEShape.iog" "Joint_1_Object_27_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_27_SINGLESG.msg" "materialInfo28.sg";
connectAttr "Joint_1_Object_27_Material_27.msg" "materialInfo28.m";
connectAttr "Image27.msg" "materialInfo28.t" -na;
connectAttr "place2dTexture28.o" "Image27.uv";
connectAttr "place2dTexture28.ofu" "Image27.ofu";
connectAttr "place2dTexture28.ofv" "Image27.ofv";
connectAttr "place2dTexture28.rf" "Image27.rf";
connectAttr "place2dTexture28.reu" "Image27.reu";
connectAttr "place2dTexture28.rev" "Image27.rev";
connectAttr "place2dTexture28.vt1" "Image27.vt1";
connectAttr "place2dTexture28.vt2" "Image27.vt2";
connectAttr "place2dTexture28.vt3" "Image27.vt3";
connectAttr "place2dTexture28.vc1" "Image27.vc1";
connectAttr "place2dTexture28.ofs" "Image27.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image27.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image27.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image27.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image27.ws";
connectAttr "Image28.oc" "Joint_1_Object_28_Material_28.c";
connectAttr "Joint_1_Object_28_Material_28.oc" "Joint_1_Object_28_SINGLESG.ss";
connectAttr "Joint_1_Object_28_SINGLEShape.iog" "Joint_1_Object_28_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_28_SINGLESG.msg" "materialInfo29.sg";
connectAttr "Joint_1_Object_28_Material_28.msg" "materialInfo29.m";
connectAttr "Image28.msg" "materialInfo29.t" -na;
connectAttr "place2dTexture29.o" "Image28.uv";
connectAttr "place2dTexture29.ofu" "Image28.ofu";
connectAttr "place2dTexture29.ofv" "Image28.ofv";
connectAttr "place2dTexture29.rf" "Image28.rf";
connectAttr "place2dTexture29.reu" "Image28.reu";
connectAttr "place2dTexture29.rev" "Image28.rev";
connectAttr "place2dTexture29.vt1" "Image28.vt1";
connectAttr "place2dTexture29.vt2" "Image28.vt2";
connectAttr "place2dTexture29.vt3" "Image28.vt3";
connectAttr "place2dTexture29.vc1" "Image28.vc1";
connectAttr "place2dTexture29.ofs" "Image28.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image28.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image28.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image28.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image28.ws";
connectAttr "Image29.oc" "Joint_1_Object_29_Material_29.c";
connectAttr "Joint_1_Object_29_Material_29.oc" "Joint_1_Object_29_SINGLESG.ss";
connectAttr "Joint_1_Object_29_SINGLEShape.iog" "Joint_1_Object_29_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_29_SINGLESG.msg" "materialInfo30.sg";
connectAttr "Joint_1_Object_29_Material_29.msg" "materialInfo30.m";
connectAttr "Image29.msg" "materialInfo30.t" -na;
connectAttr "place2dTexture30.o" "Image29.uv";
connectAttr "place2dTexture30.ofu" "Image29.ofu";
connectAttr "place2dTexture30.ofv" "Image29.ofv";
connectAttr "place2dTexture30.rf" "Image29.rf";
connectAttr "place2dTexture30.reu" "Image29.reu";
connectAttr "place2dTexture30.rev" "Image29.rev";
connectAttr "place2dTexture30.vt1" "Image29.vt1";
connectAttr "place2dTexture30.vt2" "Image29.vt2";
connectAttr "place2dTexture30.vt3" "Image29.vt3";
connectAttr "place2dTexture30.vc1" "Image29.vc1";
connectAttr "place2dTexture30.ofs" "Image29.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image29.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image29.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image29.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image29.ws";
connectAttr "Image30.oc" "Joint_1_Object_30_Material_30.c";
connectAttr "Joint_1_Object_30_Material_30.oc" "Joint_1_Object_30_SINGLESG.ss";
connectAttr "Joint_1_Object_30_SINGLEShape.iog" "Joint_1_Object_30_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_30_SINGLESG.msg" "materialInfo31.sg";
connectAttr "Joint_1_Object_30_Material_30.msg" "materialInfo31.m";
connectAttr "Image30.msg" "materialInfo31.t" -na;
connectAttr "place2dTexture31.o" "Image30.uv";
connectAttr "place2dTexture31.ofu" "Image30.ofu";
connectAttr "place2dTexture31.ofv" "Image30.ofv";
connectAttr "place2dTexture31.rf" "Image30.rf";
connectAttr "place2dTexture31.reu" "Image30.reu";
connectAttr "place2dTexture31.rev" "Image30.rev";
connectAttr "place2dTexture31.vt1" "Image30.vt1";
connectAttr "place2dTexture31.vt2" "Image30.vt2";
connectAttr "place2dTexture31.vt3" "Image30.vt3";
connectAttr "place2dTexture31.vc1" "Image30.vc1";
connectAttr "place2dTexture31.ofs" "Image30.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image30.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image30.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image30.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image30.ws";
connectAttr "Image31.oc" "Joint_1_Object_31_Material_31.c";
connectAttr "Joint_1_Object_31_Material_31.oc" "Joint_1_Object_31_SINGLESG.ss";
connectAttr "Joint_1_Object_31_SINGLEShape.iog" "Joint_1_Object_31_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_31_SINGLESG.msg" "materialInfo32.sg";
connectAttr "Joint_1_Object_31_Material_31.msg" "materialInfo32.m";
connectAttr "Image31.msg" "materialInfo32.t" -na;
connectAttr "place2dTexture32.o" "Image31.uv";
connectAttr "place2dTexture32.ofu" "Image31.ofu";
connectAttr "place2dTexture32.ofv" "Image31.ofv";
connectAttr "place2dTexture32.rf" "Image31.rf";
connectAttr "place2dTexture32.reu" "Image31.reu";
connectAttr "place2dTexture32.rev" "Image31.rev";
connectAttr "place2dTexture32.vt1" "Image31.vt1";
connectAttr "place2dTexture32.vt2" "Image31.vt2";
connectAttr "place2dTexture32.vt3" "Image31.vt3";
connectAttr "place2dTexture32.vc1" "Image31.vc1";
connectAttr "place2dTexture32.ofs" "Image31.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image31.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image31.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image31.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image31.ws";
connectAttr "Image32.oc" "Joint_1_Object_32_Material_32.c";
connectAttr "Joint_1_Object_32_Material_32.oc" "Joint_1_Object_32_SINGLESG.ss";
connectAttr "Joint_1_Object_32_SINGLEShape.iog" "Joint_1_Object_32_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_32_SINGLESG.msg" "materialInfo33.sg";
connectAttr "Joint_1_Object_32_Material_32.msg" "materialInfo33.m";
connectAttr "Image32.msg" "materialInfo33.t" -na;
connectAttr "place2dTexture33.o" "Image32.uv";
connectAttr "place2dTexture33.ofu" "Image32.ofu";
connectAttr "place2dTexture33.ofv" "Image32.ofv";
connectAttr "place2dTexture33.rf" "Image32.rf";
connectAttr "place2dTexture33.reu" "Image32.reu";
connectAttr "place2dTexture33.rev" "Image32.rev";
connectAttr "place2dTexture33.vt1" "Image32.vt1";
connectAttr "place2dTexture33.vt2" "Image32.vt2";
connectAttr "place2dTexture33.vt3" "Image32.vt3";
connectAttr "place2dTexture33.vc1" "Image32.vc1";
connectAttr "place2dTexture33.ofs" "Image32.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image32.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image32.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image32.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image32.ws";
connectAttr "Image33.oc" "Joint_1_Object_33_Material_33.c";
connectAttr "Joint_1_Object_33_Material_33.oc" "Joint_1_Object_33_SINGLESG.ss";
connectAttr "Joint_1_Object_33_SINGLEShape.iog" "Joint_1_Object_33_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_33_SINGLESG.msg" "materialInfo34.sg";
connectAttr "Joint_1_Object_33_Material_33.msg" "materialInfo34.m";
connectAttr "Image33.msg" "materialInfo34.t" -na;
connectAttr "place2dTexture34.o" "Image33.uv";
connectAttr "place2dTexture34.ofu" "Image33.ofu";
connectAttr "place2dTexture34.ofv" "Image33.ofv";
connectAttr "place2dTexture34.rf" "Image33.rf";
connectAttr "place2dTexture34.reu" "Image33.reu";
connectAttr "place2dTexture34.rev" "Image33.rev";
connectAttr "place2dTexture34.vt1" "Image33.vt1";
connectAttr "place2dTexture34.vt2" "Image33.vt2";
connectAttr "place2dTexture34.vt3" "Image33.vt3";
connectAttr "place2dTexture34.vc1" "Image33.vc1";
connectAttr "place2dTexture34.ofs" "Image33.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image33.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image33.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image33.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image33.ws";
connectAttr "Image34.oc" "Joint_1_Object_34_Material_34.c";
connectAttr "Joint_1_Object_34_Material_34.oc" "Joint_1_Object_34_SINGLESG.ss";
connectAttr "Joint_1_Object_34_SINGLEShape.iog" "Joint_1_Object_34_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_34_SINGLESG.msg" "materialInfo35.sg";
connectAttr "Joint_1_Object_34_Material_34.msg" "materialInfo35.m";
connectAttr "Image34.msg" "materialInfo35.t" -na;
connectAttr "place2dTexture35.o" "Image34.uv";
connectAttr "place2dTexture35.ofu" "Image34.ofu";
connectAttr "place2dTexture35.ofv" "Image34.ofv";
connectAttr "place2dTexture35.rf" "Image34.rf";
connectAttr "place2dTexture35.reu" "Image34.reu";
connectAttr "place2dTexture35.rev" "Image34.rev";
connectAttr "place2dTexture35.vt1" "Image34.vt1";
connectAttr "place2dTexture35.vt2" "Image34.vt2";
connectAttr "place2dTexture35.vt3" "Image34.vt3";
connectAttr "place2dTexture35.vc1" "Image34.vc1";
connectAttr "place2dTexture35.ofs" "Image34.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image34.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image34.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image34.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image34.ws";
connectAttr "Image35.oc" "Joint_1_Object_35_Material_35.c";
connectAttr "Joint_1_Object_35_Material_35.oc" "Joint_1_Object_35_SINGLESG.ss";
connectAttr "Joint_1_Object_35_SINGLEShape.iog" "Joint_1_Object_35_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_35_SINGLESG.msg" "materialInfo36.sg";
connectAttr "Joint_1_Object_35_Material_35.msg" "materialInfo36.m";
connectAttr "Image35.msg" "materialInfo36.t" -na;
connectAttr "place2dTexture36.o" "Image35.uv";
connectAttr "place2dTexture36.ofu" "Image35.ofu";
connectAttr "place2dTexture36.ofv" "Image35.ofv";
connectAttr "place2dTexture36.rf" "Image35.rf";
connectAttr "place2dTexture36.reu" "Image35.reu";
connectAttr "place2dTexture36.rev" "Image35.rev";
connectAttr "place2dTexture36.vt1" "Image35.vt1";
connectAttr "place2dTexture36.vt2" "Image35.vt2";
connectAttr "place2dTexture36.vt3" "Image35.vt3";
connectAttr "place2dTexture36.vc1" "Image35.vc1";
connectAttr "place2dTexture36.ofs" "Image35.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image35.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image35.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image35.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image35.ws";
connectAttr "Image36.oc" "Joint_1_Object_36_Material_36.c";
connectAttr "Joint_1_Object_36_Material_36.oc" "Joint_1_Object_36_SINGLESG.ss";
connectAttr "Joint_1_Object_36_SINGLEShape.iog" "Joint_1_Object_36_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_36_SINGLESG.msg" "materialInfo37.sg";
connectAttr "Joint_1_Object_36_Material_36.msg" "materialInfo37.m";
connectAttr "Image36.msg" "materialInfo37.t" -na;
connectAttr "place2dTexture37.o" "Image36.uv";
connectAttr "place2dTexture37.ofu" "Image36.ofu";
connectAttr "place2dTexture37.ofv" "Image36.ofv";
connectAttr "place2dTexture37.rf" "Image36.rf";
connectAttr "place2dTexture37.reu" "Image36.reu";
connectAttr "place2dTexture37.rev" "Image36.rev";
connectAttr "place2dTexture37.vt1" "Image36.vt1";
connectAttr "place2dTexture37.vt2" "Image36.vt2";
connectAttr "place2dTexture37.vt3" "Image36.vt3";
connectAttr "place2dTexture37.vc1" "Image36.vc1";
connectAttr "place2dTexture37.ofs" "Image36.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image36.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image36.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image36.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image36.ws";
connectAttr "Image37.oc" "Joint_1_Object_37_Material_37.c";
connectAttr "Joint_1_Object_37_Material_37.oc" "Joint_1_Object_37_SINGLESG.ss";
connectAttr "Joint_1_Object_37_SINGLEShape.iog" "Joint_1_Object_37_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_37_SINGLESG.msg" "materialInfo38.sg";
connectAttr "Joint_1_Object_37_Material_37.msg" "materialInfo38.m";
connectAttr "Image37.msg" "materialInfo38.t" -na;
connectAttr "place2dTexture38.o" "Image37.uv";
connectAttr "place2dTexture38.ofu" "Image37.ofu";
connectAttr "place2dTexture38.ofv" "Image37.ofv";
connectAttr "place2dTexture38.rf" "Image37.rf";
connectAttr "place2dTexture38.reu" "Image37.reu";
connectAttr "place2dTexture38.rev" "Image37.rev";
connectAttr "place2dTexture38.vt1" "Image37.vt1";
connectAttr "place2dTexture38.vt2" "Image37.vt2";
connectAttr "place2dTexture38.vt3" "Image37.vt3";
connectAttr "place2dTexture38.vc1" "Image37.vc1";
connectAttr "place2dTexture38.ofs" "Image37.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image37.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image37.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image37.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image37.ws";
connectAttr "Image38.oc" "Joint_1_Object_38_Material_38.c";
connectAttr "Joint_1_Object_38_Material_38.oc" "Joint_1_Object_38_SINGLESG.ss";
connectAttr "Joint_1_Object_38_SINGLEShape.iog" "Joint_1_Object_38_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_38_SINGLESG.msg" "materialInfo39.sg";
connectAttr "Joint_1_Object_38_Material_38.msg" "materialInfo39.m";
connectAttr "Image38.msg" "materialInfo39.t" -na;
connectAttr "place2dTexture39.o" "Image38.uv";
connectAttr "place2dTexture39.ofu" "Image38.ofu";
connectAttr "place2dTexture39.ofv" "Image38.ofv";
connectAttr "place2dTexture39.rf" "Image38.rf";
connectAttr "place2dTexture39.reu" "Image38.reu";
connectAttr "place2dTexture39.rev" "Image38.rev";
connectAttr "place2dTexture39.vt1" "Image38.vt1";
connectAttr "place2dTexture39.vt2" "Image38.vt2";
connectAttr "place2dTexture39.vt3" "Image38.vt3";
connectAttr "place2dTexture39.vc1" "Image38.vc1";
connectAttr "place2dTexture39.ofs" "Image38.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image38.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image38.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image38.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image38.ws";
connectAttr "Image39.oc" "Joint_1_Object_39_Material_39.c";
connectAttr "Joint_1_Object_39_Material_39.oc" "Joint_1_Object_39_SINGLESG.ss";
connectAttr "Joint_1_Object_39_SINGLEShape.iog" "Joint_1_Object_39_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_39_SINGLESG.msg" "materialInfo40.sg";
connectAttr "Joint_1_Object_39_Material_39.msg" "materialInfo40.m";
connectAttr "Image39.msg" "materialInfo40.t" -na;
connectAttr "place2dTexture40.o" "Image39.uv";
connectAttr "place2dTexture40.ofu" "Image39.ofu";
connectAttr "place2dTexture40.ofv" "Image39.ofv";
connectAttr "place2dTexture40.rf" "Image39.rf";
connectAttr "place2dTexture40.reu" "Image39.reu";
connectAttr "place2dTexture40.rev" "Image39.rev";
connectAttr "place2dTexture40.vt1" "Image39.vt1";
connectAttr "place2dTexture40.vt2" "Image39.vt2";
connectAttr "place2dTexture40.vt3" "Image39.vt3";
connectAttr "place2dTexture40.vc1" "Image39.vc1";
connectAttr "place2dTexture40.ofs" "Image39.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image39.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image39.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image39.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image39.ws";
connectAttr "Image40.oc" "Joint_1_Object_40_Material_40.c";
connectAttr "Joint_1_Object_40_Material_40.oc" "Joint_1_Object_40_SINGLESG.ss";
connectAttr "Joint_1_Object_40_SINGLEShape.iog" "Joint_1_Object_40_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_40_SINGLESG.msg" "materialInfo41.sg";
connectAttr "Joint_1_Object_40_Material_40.msg" "materialInfo41.m";
connectAttr "Image40.msg" "materialInfo41.t" -na;
connectAttr "place2dTexture41.o" "Image40.uv";
connectAttr "place2dTexture41.ofu" "Image40.ofu";
connectAttr "place2dTexture41.ofv" "Image40.ofv";
connectAttr "place2dTexture41.rf" "Image40.rf";
connectAttr "place2dTexture41.reu" "Image40.reu";
connectAttr "place2dTexture41.rev" "Image40.rev";
connectAttr "place2dTexture41.vt1" "Image40.vt1";
connectAttr "place2dTexture41.vt2" "Image40.vt2";
connectAttr "place2dTexture41.vt3" "Image40.vt3";
connectAttr "place2dTexture41.vc1" "Image40.vc1";
connectAttr "place2dTexture41.ofs" "Image40.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image40.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image40.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image40.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image40.ws";
connectAttr "Image41.oc" "Joint_1_Object_41_Material_41.c";
connectAttr "Joint_1_Object_41_Material_41.oc" "Joint_1_Object_41_SINGLESG.ss";
connectAttr "Joint_1_Object_41_SINGLEShape.iog" "Joint_1_Object_41_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_41_SINGLESG.msg" "materialInfo42.sg";
connectAttr "Joint_1_Object_41_Material_41.msg" "materialInfo42.m";
connectAttr "Image41.msg" "materialInfo42.t" -na;
connectAttr "place2dTexture42.o" "Image41.uv";
connectAttr "place2dTexture42.ofu" "Image41.ofu";
connectAttr "place2dTexture42.ofv" "Image41.ofv";
connectAttr "place2dTexture42.rf" "Image41.rf";
connectAttr "place2dTexture42.reu" "Image41.reu";
connectAttr "place2dTexture42.rev" "Image41.rev";
connectAttr "place2dTexture42.vt1" "Image41.vt1";
connectAttr "place2dTexture42.vt2" "Image41.vt2";
connectAttr "place2dTexture42.vt3" "Image41.vt3";
connectAttr "place2dTexture42.vc1" "Image41.vc1";
connectAttr "place2dTexture42.ofs" "Image41.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image41.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image41.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image41.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image41.ws";
connectAttr "Image42.oc" "Joint_1_Object_42_Material_42.c";
connectAttr "Joint_1_Object_42_Material_42.oc" "Joint_1_Object_42_SINGLESG.ss";
connectAttr "Joint_1_Object_42_SINGLEShape.iog" "Joint_1_Object_42_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_42_SINGLESG.msg" "materialInfo43.sg";
connectAttr "Joint_1_Object_42_Material_42.msg" "materialInfo43.m";
connectAttr "Image42.msg" "materialInfo43.t" -na;
connectAttr "place2dTexture43.o" "Image42.uv";
connectAttr "place2dTexture43.ofu" "Image42.ofu";
connectAttr "place2dTexture43.ofv" "Image42.ofv";
connectAttr "place2dTexture43.rf" "Image42.rf";
connectAttr "place2dTexture43.reu" "Image42.reu";
connectAttr "place2dTexture43.rev" "Image42.rev";
connectAttr "place2dTexture43.vt1" "Image42.vt1";
connectAttr "place2dTexture43.vt2" "Image42.vt2";
connectAttr "place2dTexture43.vt3" "Image42.vt3";
connectAttr "place2dTexture43.vc1" "Image42.vc1";
connectAttr "place2dTexture43.ofs" "Image42.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image42.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image42.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image42.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image42.ws";
connectAttr "Image43.oc" "Joint_1_Object_43_Material_43.c";
connectAttr "Joint_1_Object_43_Material_43.oc" "Joint_1_Object_43_SINGLESG.ss";
connectAttr "Joint_1_Object_43_SINGLEShape.iog" "Joint_1_Object_43_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_43_SINGLESG.msg" "materialInfo44.sg";
connectAttr "Joint_1_Object_43_Material_43.msg" "materialInfo44.m";
connectAttr "Image43.msg" "materialInfo44.t" -na;
connectAttr "place2dTexture44.o" "Image43.uv";
connectAttr "place2dTexture44.ofu" "Image43.ofu";
connectAttr "place2dTexture44.ofv" "Image43.ofv";
connectAttr "place2dTexture44.rf" "Image43.rf";
connectAttr "place2dTexture44.reu" "Image43.reu";
connectAttr "place2dTexture44.rev" "Image43.rev";
connectAttr "place2dTexture44.vt1" "Image43.vt1";
connectAttr "place2dTexture44.vt2" "Image43.vt2";
connectAttr "place2dTexture44.vt3" "Image43.vt3";
connectAttr "place2dTexture44.vc1" "Image43.vc1";
connectAttr "place2dTexture44.ofs" "Image43.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image43.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image43.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image43.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image43.ws";
connectAttr "Image44.oc" "Joint_1_Object_44_Material_44.c";
connectAttr "Joint_1_Object_44_Material_44.oc" "Joint_1_Object_44_SINGLESG.ss";
connectAttr "Joint_1_Object_44_SINGLEShape.iog" "Joint_1_Object_44_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_44_SINGLESG.msg" "materialInfo45.sg";
connectAttr "Joint_1_Object_44_Material_44.msg" "materialInfo45.m";
connectAttr "Image44.msg" "materialInfo45.t" -na;
connectAttr "place2dTexture45.o" "Image44.uv";
connectAttr "place2dTexture45.ofu" "Image44.ofu";
connectAttr "place2dTexture45.ofv" "Image44.ofv";
connectAttr "place2dTexture45.rf" "Image44.rf";
connectAttr "place2dTexture45.reu" "Image44.reu";
connectAttr "place2dTexture45.rev" "Image44.rev";
connectAttr "place2dTexture45.vt1" "Image44.vt1";
connectAttr "place2dTexture45.vt2" "Image44.vt2";
connectAttr "place2dTexture45.vt3" "Image44.vt3";
connectAttr "place2dTexture45.vc1" "Image44.vc1";
connectAttr "place2dTexture45.ofs" "Image44.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image44.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image44.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image44.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image44.ws";
connectAttr "Image45.oc" "Joint_1_Object_45_Material_45.c";
connectAttr "Joint_1_Object_45_Material_45.oc" "Joint_1_Object_45_SINGLESG.ss";
connectAttr "Joint_1_Object_45_SINGLEShape.iog" "Joint_1_Object_45_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_45_SINGLESG.msg" "materialInfo46.sg";
connectAttr "Joint_1_Object_45_Material_45.msg" "materialInfo46.m";
connectAttr "Image45.msg" "materialInfo46.t" -na;
connectAttr "place2dTexture46.o" "Image45.uv";
connectAttr "place2dTexture46.ofu" "Image45.ofu";
connectAttr "place2dTexture46.ofv" "Image45.ofv";
connectAttr "place2dTexture46.rf" "Image45.rf";
connectAttr "place2dTexture46.reu" "Image45.reu";
connectAttr "place2dTexture46.rev" "Image45.rev";
connectAttr "place2dTexture46.vt1" "Image45.vt1";
connectAttr "place2dTexture46.vt2" "Image45.vt2";
connectAttr "place2dTexture46.vt3" "Image45.vt3";
connectAttr "place2dTexture46.vc1" "Image45.vc1";
connectAttr "place2dTexture46.ofs" "Image45.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image45.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image45.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image45.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image45.ws";
connectAttr "Image46.oc" "Joint_1_Object_46_Material_46.c";
connectAttr "Joint_1_Object_46_Material_46.oc" "Joint_1_Object_46_SINGLESG.ss";
connectAttr "Joint_1_Object_46_SINGLEShape.iog" "Joint_1_Object_46_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_46_SINGLESG.msg" "materialInfo47.sg";
connectAttr "Joint_1_Object_46_Material_46.msg" "materialInfo47.m";
connectAttr "Image46.msg" "materialInfo47.t" -na;
connectAttr "place2dTexture47.o" "Image46.uv";
connectAttr "place2dTexture47.ofu" "Image46.ofu";
connectAttr "place2dTexture47.ofv" "Image46.ofv";
connectAttr "place2dTexture47.rf" "Image46.rf";
connectAttr "place2dTexture47.reu" "Image46.reu";
connectAttr "place2dTexture47.rev" "Image46.rev";
connectAttr "place2dTexture47.vt1" "Image46.vt1";
connectAttr "place2dTexture47.vt2" "Image46.vt2";
connectAttr "place2dTexture47.vt3" "Image46.vt3";
connectAttr "place2dTexture47.vc1" "Image46.vc1";
connectAttr "place2dTexture47.ofs" "Image46.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image46.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image46.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image46.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image46.ws";
connectAttr "Image47.oc" "Joint_1_Object_47_Material_47.c";
connectAttr "Joint_1_Object_47_Material_47.oc" "Joint_1_Object_47_SINGLESG.ss";
connectAttr "Joint_1_Object_47_SINGLEShape.iog" "Joint_1_Object_47_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_47_SINGLESG.msg" "materialInfo48.sg";
connectAttr "Joint_1_Object_47_Material_47.msg" "materialInfo48.m";
connectAttr "Image47.msg" "materialInfo48.t" -na;
connectAttr "place2dTexture48.o" "Image47.uv";
connectAttr "place2dTexture48.ofu" "Image47.ofu";
connectAttr "place2dTexture48.ofv" "Image47.ofv";
connectAttr "place2dTexture48.rf" "Image47.rf";
connectAttr "place2dTexture48.reu" "Image47.reu";
connectAttr "place2dTexture48.rev" "Image47.rev";
connectAttr "place2dTexture48.vt1" "Image47.vt1";
connectAttr "place2dTexture48.vt2" "Image47.vt2";
connectAttr "place2dTexture48.vt3" "Image47.vt3";
connectAttr "place2dTexture48.vc1" "Image47.vc1";
connectAttr "place2dTexture48.ofs" "Image47.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image47.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image47.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image47.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image47.ws";
connectAttr "Image48.oc" "Joint_1_Object_48_Material_48.c";
connectAttr "Joint_1_Object_48_Material_48.oc" "Joint_1_Object_48_SINGLESG.ss";
connectAttr "Joint_1_Object_48_SINGLEShape.iog" "Joint_1_Object_48_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_48_SINGLESG.msg" "materialInfo49.sg";
connectAttr "Joint_1_Object_48_Material_48.msg" "materialInfo49.m";
connectAttr "Image48.msg" "materialInfo49.t" -na;
connectAttr "place2dTexture49.o" "Image48.uv";
connectAttr "place2dTexture49.ofu" "Image48.ofu";
connectAttr "place2dTexture49.ofv" "Image48.ofv";
connectAttr "place2dTexture49.rf" "Image48.rf";
connectAttr "place2dTexture49.reu" "Image48.reu";
connectAttr "place2dTexture49.rev" "Image48.rev";
connectAttr "place2dTexture49.vt1" "Image48.vt1";
connectAttr "place2dTexture49.vt2" "Image48.vt2";
connectAttr "place2dTexture49.vt3" "Image48.vt3";
connectAttr "place2dTexture49.vc1" "Image48.vc1";
connectAttr "place2dTexture49.ofs" "Image48.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image48.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image48.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image48.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image48.ws";
connectAttr "Image49.oc" "Joint_1_Object_49_Material_49.c";
connectAttr "Joint_1_Object_49_Material_49.oc" "Joint_1_Object_49_SINGLESG.ss";
connectAttr "Joint_1_Object_49_SINGLEShape.iog" "Joint_1_Object_49_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_49_SINGLESG.msg" "materialInfo50.sg";
connectAttr "Joint_1_Object_49_Material_49.msg" "materialInfo50.m";
connectAttr "Image49.msg" "materialInfo50.t" -na;
connectAttr "place2dTexture50.o" "Image49.uv";
connectAttr "place2dTexture50.ofu" "Image49.ofu";
connectAttr "place2dTexture50.ofv" "Image49.ofv";
connectAttr "place2dTexture50.rf" "Image49.rf";
connectAttr "place2dTexture50.reu" "Image49.reu";
connectAttr "place2dTexture50.rev" "Image49.rev";
connectAttr "place2dTexture50.vt1" "Image49.vt1";
connectAttr "place2dTexture50.vt2" "Image49.vt2";
connectAttr "place2dTexture50.vt3" "Image49.vt3";
connectAttr "place2dTexture50.vc1" "Image49.vc1";
connectAttr "place2dTexture50.ofs" "Image49.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image49.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image49.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image49.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image49.ws";
connectAttr "Image50.oc" "Joint_1_Object_50_Material_50.c";
connectAttr "Joint_1_Object_50_Material_50.oc" "Joint_1_Object_50_SINGLESG.ss";
connectAttr "Joint_1_Object_50_SINGLEShape.iog" "Joint_1_Object_50_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_50_SINGLESG.msg" "materialInfo51.sg";
connectAttr "Joint_1_Object_50_Material_50.msg" "materialInfo51.m";
connectAttr "Image50.msg" "materialInfo51.t" -na;
connectAttr "place2dTexture51.o" "Image50.uv";
connectAttr "place2dTexture51.ofu" "Image50.ofu";
connectAttr "place2dTexture51.ofv" "Image50.ofv";
connectAttr "place2dTexture51.rf" "Image50.rf";
connectAttr "place2dTexture51.reu" "Image50.reu";
connectAttr "place2dTexture51.rev" "Image50.rev";
connectAttr "place2dTexture51.vt1" "Image50.vt1";
connectAttr "place2dTexture51.vt2" "Image50.vt2";
connectAttr "place2dTexture51.vt3" "Image50.vt3";
connectAttr "place2dTexture51.vc1" "Image50.vc1";
connectAttr "place2dTexture51.ofs" "Image50.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image50.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image50.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image50.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image50.ws";
connectAttr "Image51.oc" "Joint_1_Object_51_Material_51.c";
connectAttr "Joint_1_Object_51_Material_51.oc" "Joint_1_Object_51_SINGLESG.ss";
connectAttr "Joint_1_Object_51_SINGLEShape.iog" "Joint_1_Object_51_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_51_SINGLESG.msg" "materialInfo52.sg";
connectAttr "Joint_1_Object_51_Material_51.msg" "materialInfo52.m";
connectAttr "Image51.msg" "materialInfo52.t" -na;
connectAttr "place2dTexture52.o" "Image51.uv";
connectAttr "place2dTexture52.ofu" "Image51.ofu";
connectAttr "place2dTexture52.ofv" "Image51.ofv";
connectAttr "place2dTexture52.rf" "Image51.rf";
connectAttr "place2dTexture52.reu" "Image51.reu";
connectAttr "place2dTexture52.rev" "Image51.rev";
connectAttr "place2dTexture52.vt1" "Image51.vt1";
connectAttr "place2dTexture52.vt2" "Image51.vt2";
connectAttr "place2dTexture52.vt3" "Image51.vt3";
connectAttr "place2dTexture52.vc1" "Image51.vc1";
connectAttr "place2dTexture52.ofs" "Image51.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image51.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image51.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image51.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image51.ws";
connectAttr "Image52.oc" "Joint_1_Object_52_Material_52.c";
connectAttr "Joint_1_Object_52_Material_52.oc" "Joint_1_Object_52_SINGLESG.ss";
connectAttr "Joint_1_Object_52_SINGLEShape.iog" "Joint_1_Object_52_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_52_SINGLESG.msg" "materialInfo53.sg";
connectAttr "Joint_1_Object_52_Material_52.msg" "materialInfo53.m";
connectAttr "Image52.msg" "materialInfo53.t" -na;
connectAttr "place2dTexture53.o" "Image52.uv";
connectAttr "place2dTexture53.ofu" "Image52.ofu";
connectAttr "place2dTexture53.ofv" "Image52.ofv";
connectAttr "place2dTexture53.rf" "Image52.rf";
connectAttr "place2dTexture53.reu" "Image52.reu";
connectAttr "place2dTexture53.rev" "Image52.rev";
connectAttr "place2dTexture53.vt1" "Image52.vt1";
connectAttr "place2dTexture53.vt2" "Image52.vt2";
connectAttr "place2dTexture53.vt3" "Image52.vt3";
connectAttr "place2dTexture53.vc1" "Image52.vc1";
connectAttr "place2dTexture53.ofs" "Image52.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image52.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image52.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image52.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image52.ws";
connectAttr "Image53.oc" "Joint_1_Object_53_Material_53.c";
connectAttr "Joint_1_Object_53_Material_53.oc" "Joint_1_Object_53_SINGLESG.ss";
connectAttr "Joint_1_Object_53_SINGLEShape.iog" "Joint_1_Object_53_SINGLESG.dsm"
		 -na;
connectAttr "Joint_1_Object_53_SINGLESG.msg" "materialInfo54.sg";
connectAttr "Joint_1_Object_53_Material_53.msg" "materialInfo54.m";
connectAttr "Image53.msg" "materialInfo54.t" -na;
connectAttr "place2dTexture54.o" "Image53.uv";
connectAttr "place2dTexture54.ofu" "Image53.ofu";
connectAttr "place2dTexture54.ofv" "Image53.ofv";
connectAttr "place2dTexture54.rf" "Image53.rf";
connectAttr "place2dTexture54.reu" "Image53.reu";
connectAttr "place2dTexture54.rev" "Image53.rev";
connectAttr "place2dTexture54.vt1" "Image53.vt1";
connectAttr "place2dTexture54.vt2" "Image53.vt2";
connectAttr "place2dTexture54.vt3" "Image53.vt3";
connectAttr "place2dTexture54.vc1" "Image53.vc1";
connectAttr "place2dTexture54.ofs" "Image53.fs";
connectAttr ":defaultColorMgtGlobals.cme" "Image53.cme";
connectAttr ":defaultColorMgtGlobals.cfe" "Image53.cmcf";
connectAttr ":defaultColorMgtGlobals.cfp" "Image53.cmcp";
connectAttr ":defaultColorMgtGlobals.wsn" "Image53.ws";
connectAttr "skinCluster1GroupParts.og" "skinCluster1.ip[0].ig";
connectAttr "skinCluster1GroupId.id" "skinCluster1.ip[0].gi";
connectAttr "bindPose1.msg" "skinCluster1.bp";
connectAttr "JOBJ_1.wm" "skinCluster1.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster1.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster1.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster1.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster1.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster1.ifcl[1]";
connectAttr "groupParts2.og" "tweak1.ip[0].ig";
connectAttr "groupId2.id" "tweak1.ip[0].gi";
connectAttr "skinCluster1GroupId.msg" "skinCluster1Set.gn" -na;
connectAttr "Joint_1_Object_0_SINGLEShape.iog.og[0]" "skinCluster1Set.dsm" -na;
connectAttr "skinCluster1.msg" "skinCluster1Set.ub[0]";
connectAttr "tweak1.og[0]" "skinCluster1GroupParts.ig";
connectAttr "skinCluster1GroupId.id" "skinCluster1GroupParts.gi";
connectAttr "groupId2.msg" "tweakSet1.gn" -na;
connectAttr "Joint_1_Object_0_SINGLEShape.iog.og[1]" "tweakSet1.dsm" -na;
connectAttr "tweak1.msg" "tweakSet1.ub[0]";
connectAttr "Joint_1_Object_0_SINGLEShapeOrig.w" "groupParts2.ig";
connectAttr "groupId2.id" "groupParts2.gi";
connectAttr "JOBJ_0.msg" "bindPose1.m[0]";
connectAttr "JOBJ_1.msg" "bindPose1.m[1]";
connectAttr "bindPose1.w" "bindPose1.p[0]";
connectAttr "bindPose1.m[0]" "bindPose1.p[1]";
connectAttr "JOBJ_0.bps" "bindPose1.wm[0]";
connectAttr "JOBJ_1.bps" "bindPose1.wm[1]";
connectAttr "skinCluster2GroupParts.og" "skinCluster2.ip[0].ig";
connectAttr "skinCluster2GroupId.id" "skinCluster2.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster2.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster2.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster2.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster2.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster2.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster2.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster2.bp";
connectAttr "groupParts4.og" "tweak2.ip[0].ig";
connectAttr "groupId4.id" "tweak2.ip[0].gi";
connectAttr "skinCluster2GroupId.msg" "skinCluster2Set.gn" -na;
connectAttr "Joint_1_Object_1_SINGLEShape.iog.og[0]" "skinCluster2Set.dsm" -na;
connectAttr "skinCluster2.msg" "skinCluster2Set.ub[0]";
connectAttr "tweak2.og[0]" "skinCluster2GroupParts.ig";
connectAttr "skinCluster2GroupId.id" "skinCluster2GroupParts.gi";
connectAttr "groupId4.msg" "tweakSet2.gn" -na;
connectAttr "Joint_1_Object_1_SINGLEShape.iog.og[1]" "tweakSet2.dsm" -na;
connectAttr "tweak2.msg" "tweakSet2.ub[0]";
connectAttr "Joint_1_Object_1_SINGLEShapeOrig.w" "groupParts4.ig";
connectAttr "groupId4.id" "groupParts4.gi";
connectAttr "skinCluster3GroupParts.og" "skinCluster3.ip[0].ig";
connectAttr "skinCluster3GroupId.id" "skinCluster3.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster3.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster3.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster3.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster3.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster3.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster3.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster3.bp";
connectAttr "groupParts6.og" "tweak3.ip[0].ig";
connectAttr "groupId6.id" "tweak3.ip[0].gi";
connectAttr "skinCluster3GroupId.msg" "skinCluster3Set.gn" -na;
connectAttr "Joint_1_Object_10_SINGLEShape.iog.og[0]" "skinCluster3Set.dsm" -na;
connectAttr "skinCluster3.msg" "skinCluster3Set.ub[0]";
connectAttr "tweak3.og[0]" "skinCluster3GroupParts.ig";
connectAttr "skinCluster3GroupId.id" "skinCluster3GroupParts.gi";
connectAttr "groupId6.msg" "tweakSet3.gn" -na;
connectAttr "Joint_1_Object_10_SINGLEShape.iog.og[1]" "tweakSet3.dsm" -na;
connectAttr "tweak3.msg" "tweakSet3.ub[0]";
connectAttr "Joint_1_Object_10_SINGLEShapeOrig.w" "groupParts6.ig";
connectAttr "groupId6.id" "groupParts6.gi";
connectAttr "skinCluster4GroupParts.og" "skinCluster4.ip[0].ig";
connectAttr "skinCluster4GroupId.id" "skinCluster4.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster4.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster4.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster4.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster4.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster4.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster4.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster4.bp";
connectAttr "groupParts8.og" "tweak4.ip[0].ig";
connectAttr "groupId8.id" "tweak4.ip[0].gi";
connectAttr "skinCluster4GroupId.msg" "skinCluster4Set.gn" -na;
connectAttr "Joint_1_Object_11_SINGLEShape.iog.og[0]" "skinCluster4Set.dsm" -na;
connectAttr "skinCluster4.msg" "skinCluster4Set.ub[0]";
connectAttr "tweak4.og[0]" "skinCluster4GroupParts.ig";
connectAttr "skinCluster4GroupId.id" "skinCluster4GroupParts.gi";
connectAttr "groupId8.msg" "tweakSet4.gn" -na;
connectAttr "Joint_1_Object_11_SINGLEShape.iog.og[1]" "tweakSet4.dsm" -na;
connectAttr "tweak4.msg" "tweakSet4.ub[0]";
connectAttr "Joint_1_Object_11_SINGLEShapeOrig.w" "groupParts8.ig";
connectAttr "groupId8.id" "groupParts8.gi";
connectAttr "skinCluster5GroupParts.og" "skinCluster5.ip[0].ig";
connectAttr "skinCluster5GroupId.id" "skinCluster5.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster5.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster5.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster5.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster5.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster5.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster5.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster5.bp";
connectAttr "groupParts10.og" "tweak5.ip[0].ig";
connectAttr "groupId10.id" "tweak5.ip[0].gi";
connectAttr "skinCluster5GroupId.msg" "skinCluster5Set.gn" -na;
connectAttr "Joint_1_Object_12_SINGLEShape.iog.og[0]" "skinCluster5Set.dsm" -na;
connectAttr "skinCluster5.msg" "skinCluster5Set.ub[0]";
connectAttr "tweak5.og[0]" "skinCluster5GroupParts.ig";
connectAttr "skinCluster5GroupId.id" "skinCluster5GroupParts.gi";
connectAttr "groupId10.msg" "tweakSet5.gn" -na;
connectAttr "Joint_1_Object_12_SINGLEShape.iog.og[1]" "tweakSet5.dsm" -na;
connectAttr "tweak5.msg" "tweakSet5.ub[0]";
connectAttr "Joint_1_Object_12_SINGLEShapeOrig.w" "groupParts10.ig";
connectAttr "groupId10.id" "groupParts10.gi";
connectAttr "skinCluster6GroupParts.og" "skinCluster6.ip[0].ig";
connectAttr "skinCluster6GroupId.id" "skinCluster6.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster6.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster6.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster6.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster6.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster6.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster6.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster6.bp";
connectAttr "groupParts12.og" "tweak6.ip[0].ig";
connectAttr "groupId12.id" "tweak6.ip[0].gi";
connectAttr "skinCluster6GroupId.msg" "skinCluster6Set.gn" -na;
connectAttr "Joint_1_Object_13_SINGLEShape.iog.og[0]" "skinCluster6Set.dsm" -na;
connectAttr "skinCluster6.msg" "skinCluster6Set.ub[0]";
connectAttr "tweak6.og[0]" "skinCluster6GroupParts.ig";
connectAttr "skinCluster6GroupId.id" "skinCluster6GroupParts.gi";
connectAttr "groupId12.msg" "tweakSet6.gn" -na;
connectAttr "Joint_1_Object_13_SINGLEShape.iog.og[1]" "tweakSet6.dsm" -na;
connectAttr "tweak6.msg" "tweakSet6.ub[0]";
connectAttr "Joint_1_Object_13_SINGLEShapeOrig.w" "groupParts12.ig";
connectAttr "groupId12.id" "groupParts12.gi";
connectAttr "skinCluster7GroupParts.og" "skinCluster7.ip[0].ig";
connectAttr "skinCluster7GroupId.id" "skinCluster7.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster7.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster7.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster7.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster7.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster7.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster7.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster7.bp";
connectAttr "groupParts14.og" "tweak7.ip[0].ig";
connectAttr "groupId14.id" "tweak7.ip[0].gi";
connectAttr "skinCluster7GroupId.msg" "skinCluster7Set.gn" -na;
connectAttr "Joint_1_Object_14_SINGLEShape.iog.og[0]" "skinCluster7Set.dsm" -na;
connectAttr "skinCluster7.msg" "skinCluster7Set.ub[0]";
connectAttr "tweak7.og[0]" "skinCluster7GroupParts.ig";
connectAttr "skinCluster7GroupId.id" "skinCluster7GroupParts.gi";
connectAttr "groupId14.msg" "tweakSet7.gn" -na;
connectAttr "Joint_1_Object_14_SINGLEShape.iog.og[1]" "tweakSet7.dsm" -na;
connectAttr "tweak7.msg" "tweakSet7.ub[0]";
connectAttr "Joint_1_Object_14_SINGLEShapeOrig.w" "groupParts14.ig";
connectAttr "groupId14.id" "groupParts14.gi";
connectAttr "skinCluster8GroupParts.og" "skinCluster8.ip[0].ig";
connectAttr "skinCluster8GroupId.id" "skinCluster8.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster8.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster8.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster8.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster8.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster8.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster8.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster8.bp";
connectAttr "groupParts16.og" "tweak8.ip[0].ig";
connectAttr "groupId16.id" "tweak8.ip[0].gi";
connectAttr "skinCluster8GroupId.msg" "skinCluster8Set.gn" -na;
connectAttr "Joint_1_Object_15_SINGLEShape.iog.og[0]" "skinCluster8Set.dsm" -na;
connectAttr "skinCluster8.msg" "skinCluster8Set.ub[0]";
connectAttr "tweak8.og[0]" "skinCluster8GroupParts.ig";
connectAttr "skinCluster8GroupId.id" "skinCluster8GroupParts.gi";
connectAttr "groupId16.msg" "tweakSet8.gn" -na;
connectAttr "Joint_1_Object_15_SINGLEShape.iog.og[1]" "tweakSet8.dsm" -na;
connectAttr "tweak8.msg" "tweakSet8.ub[0]";
connectAttr "Joint_1_Object_15_SINGLEShapeOrig.w" "groupParts16.ig";
connectAttr "groupId16.id" "groupParts16.gi";
connectAttr "skinCluster9GroupParts.og" "skinCluster9.ip[0].ig";
connectAttr "skinCluster9GroupId.id" "skinCluster9.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster9.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster9.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster9.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster9.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster9.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster9.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster9.bp";
connectAttr "groupParts18.og" "tweak9.ip[0].ig";
connectAttr "groupId18.id" "tweak9.ip[0].gi";
connectAttr "skinCluster9GroupId.msg" "skinCluster9Set.gn" -na;
connectAttr "Joint_1_Object_16_SINGLEShape.iog.og[0]" "skinCluster9Set.dsm" -na;
connectAttr "skinCluster9.msg" "skinCluster9Set.ub[0]";
connectAttr "tweak9.og[0]" "skinCluster9GroupParts.ig";
connectAttr "skinCluster9GroupId.id" "skinCluster9GroupParts.gi";
connectAttr "groupId18.msg" "tweakSet9.gn" -na;
connectAttr "Joint_1_Object_16_SINGLEShape.iog.og[1]" "tweakSet9.dsm" -na;
connectAttr "tweak9.msg" "tweakSet9.ub[0]";
connectAttr "Joint_1_Object_16_SINGLEShapeOrig.w" "groupParts18.ig";
connectAttr "groupId18.id" "groupParts18.gi";
connectAttr "skinCluster10GroupParts.og" "skinCluster10.ip[0].ig";
connectAttr "skinCluster10GroupId.id" "skinCluster10.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster10.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster10.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster10.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster10.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster10.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster10.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster10.bp";
connectAttr "groupParts20.og" "tweak10.ip[0].ig";
connectAttr "groupId20.id" "tweak10.ip[0].gi";
connectAttr "skinCluster10GroupId.msg" "skinCluster10Set.gn" -na;
connectAttr "Joint_1_Object_17_SINGLEShape.iog.og[0]" "skinCluster10Set.dsm" -na
		;
connectAttr "skinCluster10.msg" "skinCluster10Set.ub[0]";
connectAttr "tweak10.og[0]" "skinCluster10GroupParts.ig";
connectAttr "skinCluster10GroupId.id" "skinCluster10GroupParts.gi";
connectAttr "groupId20.msg" "tweakSet10.gn" -na;
connectAttr "Joint_1_Object_17_SINGLEShape.iog.og[1]" "tweakSet10.dsm" -na;
connectAttr "tweak10.msg" "tweakSet10.ub[0]";
connectAttr "Joint_1_Object_17_SINGLEShapeOrig.w" "groupParts20.ig";
connectAttr "groupId20.id" "groupParts20.gi";
connectAttr "skinCluster11GroupParts.og" "skinCluster11.ip[0].ig";
connectAttr "skinCluster11GroupId.id" "skinCluster11.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster11.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster11.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster11.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster11.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster11.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster11.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster11.bp";
connectAttr "groupParts22.og" "tweak11.ip[0].ig";
connectAttr "groupId22.id" "tweak11.ip[0].gi";
connectAttr "skinCluster11GroupId.msg" "skinCluster11Set.gn" -na;
connectAttr "Joint_1_Object_18_SINGLEShape.iog.og[0]" "skinCluster11Set.dsm" -na
		;
connectAttr "skinCluster11.msg" "skinCluster11Set.ub[0]";
connectAttr "tweak11.og[0]" "skinCluster11GroupParts.ig";
connectAttr "skinCluster11GroupId.id" "skinCluster11GroupParts.gi";
connectAttr "groupId22.msg" "tweakSet11.gn" -na;
connectAttr "Joint_1_Object_18_SINGLEShape.iog.og[1]" "tweakSet11.dsm" -na;
connectAttr "tweak11.msg" "tweakSet11.ub[0]";
connectAttr "Joint_1_Object_18_SINGLEShapeOrig.w" "groupParts22.ig";
connectAttr "groupId22.id" "groupParts22.gi";
connectAttr "skinCluster12GroupParts.og" "skinCluster12.ip[0].ig";
connectAttr "skinCluster12GroupId.id" "skinCluster12.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster12.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster12.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster12.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster12.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster12.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster12.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster12.bp";
connectAttr "groupParts24.og" "tweak12.ip[0].ig";
connectAttr "groupId24.id" "tweak12.ip[0].gi";
connectAttr "skinCluster12GroupId.msg" "skinCluster12Set.gn" -na;
connectAttr "Joint_1_Object_19_SINGLEShape.iog.og[0]" "skinCluster12Set.dsm" -na
		;
connectAttr "skinCluster12.msg" "skinCluster12Set.ub[0]";
connectAttr "tweak12.og[0]" "skinCluster12GroupParts.ig";
connectAttr "skinCluster12GroupId.id" "skinCluster12GroupParts.gi";
connectAttr "groupId24.msg" "tweakSet12.gn" -na;
connectAttr "Joint_1_Object_19_SINGLEShape.iog.og[1]" "tweakSet12.dsm" -na;
connectAttr "tweak12.msg" "tweakSet12.ub[0]";
connectAttr "Joint_1_Object_19_SINGLEShapeOrig.w" "groupParts24.ig";
connectAttr "groupId24.id" "groupParts24.gi";
connectAttr "skinCluster13GroupParts.og" "skinCluster13.ip[0].ig";
connectAttr "skinCluster13GroupId.id" "skinCluster13.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster13.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster13.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster13.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster13.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster13.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster13.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster13.bp";
connectAttr "groupParts26.og" "tweak13.ip[0].ig";
connectAttr "groupId26.id" "tweak13.ip[0].gi";
connectAttr "skinCluster13GroupId.msg" "skinCluster13Set.gn" -na;
connectAttr "Joint_1_Object_2_SINGLEShape.iog.og[0]" "skinCluster13Set.dsm" -na;
connectAttr "skinCluster13.msg" "skinCluster13Set.ub[0]";
connectAttr "tweak13.og[0]" "skinCluster13GroupParts.ig";
connectAttr "skinCluster13GroupId.id" "skinCluster13GroupParts.gi";
connectAttr "groupId26.msg" "tweakSet13.gn" -na;
connectAttr "Joint_1_Object_2_SINGLEShape.iog.og[1]" "tweakSet13.dsm" -na;
connectAttr "tweak13.msg" "tweakSet13.ub[0]";
connectAttr "Joint_1_Object_2_SINGLEShapeOrig.w" "groupParts26.ig";
connectAttr "groupId26.id" "groupParts26.gi";
connectAttr "skinCluster14GroupParts.og" "skinCluster14.ip[0].ig";
connectAttr "skinCluster14GroupId.id" "skinCluster14.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster14.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster14.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster14.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster14.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster14.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster14.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster14.bp";
connectAttr "groupParts28.og" "tweak14.ip[0].ig";
connectAttr "groupId28.id" "tweak14.ip[0].gi";
connectAttr "skinCluster14GroupId.msg" "skinCluster14Set.gn" -na;
connectAttr "Joint_1_Object_20_SINGLEShape.iog.og[0]" "skinCluster14Set.dsm" -na
		;
connectAttr "skinCluster14.msg" "skinCluster14Set.ub[0]";
connectAttr "tweak14.og[0]" "skinCluster14GroupParts.ig";
connectAttr "skinCluster14GroupId.id" "skinCluster14GroupParts.gi";
connectAttr "groupId28.msg" "tweakSet14.gn" -na;
connectAttr "Joint_1_Object_20_SINGLEShape.iog.og[1]" "tweakSet14.dsm" -na;
connectAttr "tweak14.msg" "tweakSet14.ub[0]";
connectAttr "Joint_1_Object_20_SINGLEShapeOrig.w" "groupParts28.ig";
connectAttr "groupId28.id" "groupParts28.gi";
connectAttr "skinCluster15GroupParts.og" "skinCluster15.ip[0].ig";
connectAttr "skinCluster15GroupId.id" "skinCluster15.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster15.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster15.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster15.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster15.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster15.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster15.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster15.bp";
connectAttr "groupParts30.og" "tweak15.ip[0].ig";
connectAttr "groupId30.id" "tweak15.ip[0].gi";
connectAttr "skinCluster15GroupId.msg" "skinCluster15Set.gn" -na;
connectAttr "Joint_1_Object_21_SINGLEShape.iog.og[0]" "skinCluster15Set.dsm" -na
		;
connectAttr "skinCluster15.msg" "skinCluster15Set.ub[0]";
connectAttr "tweak15.og[0]" "skinCluster15GroupParts.ig";
connectAttr "skinCluster15GroupId.id" "skinCluster15GroupParts.gi";
connectAttr "groupId30.msg" "tweakSet15.gn" -na;
connectAttr "Joint_1_Object_21_SINGLEShape.iog.og[1]" "tweakSet15.dsm" -na;
connectAttr "tweak15.msg" "tweakSet15.ub[0]";
connectAttr "Joint_1_Object_21_SINGLEShapeOrig.w" "groupParts30.ig";
connectAttr "groupId30.id" "groupParts30.gi";
connectAttr "skinCluster16GroupParts.og" "skinCluster16.ip[0].ig";
connectAttr "skinCluster16GroupId.id" "skinCluster16.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster16.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster16.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster16.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster16.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster16.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster16.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster16.bp";
connectAttr "groupParts32.og" "tweak16.ip[0].ig";
connectAttr "groupId32.id" "tweak16.ip[0].gi";
connectAttr "skinCluster16GroupId.msg" "skinCluster16Set.gn" -na;
connectAttr "Joint_1_Object_22_SINGLEShape.iog.og[0]" "skinCluster16Set.dsm" -na
		;
connectAttr "skinCluster16.msg" "skinCluster16Set.ub[0]";
connectAttr "tweak16.og[0]" "skinCluster16GroupParts.ig";
connectAttr "skinCluster16GroupId.id" "skinCluster16GroupParts.gi";
connectAttr "groupId32.msg" "tweakSet16.gn" -na;
connectAttr "Joint_1_Object_22_SINGLEShape.iog.og[1]" "tweakSet16.dsm" -na;
connectAttr "tweak16.msg" "tweakSet16.ub[0]";
connectAttr "Joint_1_Object_22_SINGLEShapeOrig.w" "groupParts32.ig";
connectAttr "groupId32.id" "groupParts32.gi";
connectAttr "skinCluster17GroupParts.og" "skinCluster17.ip[0].ig";
connectAttr "skinCluster17GroupId.id" "skinCluster17.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster17.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster17.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster17.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster17.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster17.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster17.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster17.bp";
connectAttr "groupParts34.og" "tweak17.ip[0].ig";
connectAttr "groupId34.id" "tweak17.ip[0].gi";
connectAttr "skinCluster17GroupId.msg" "skinCluster17Set.gn" -na;
connectAttr "Joint_1_Object_23_SINGLEShape.iog.og[0]" "skinCluster17Set.dsm" -na
		;
connectAttr "skinCluster17.msg" "skinCluster17Set.ub[0]";
connectAttr "tweak17.og[0]" "skinCluster17GroupParts.ig";
connectAttr "skinCluster17GroupId.id" "skinCluster17GroupParts.gi";
connectAttr "groupId34.msg" "tweakSet17.gn" -na;
connectAttr "Joint_1_Object_23_SINGLEShape.iog.og[1]" "tweakSet17.dsm" -na;
connectAttr "tweak17.msg" "tweakSet17.ub[0]";
connectAttr "Joint_1_Object_23_SINGLEShapeOrig.w" "groupParts34.ig";
connectAttr "groupId34.id" "groupParts34.gi";
connectAttr "skinCluster18GroupParts.og" "skinCluster18.ip[0].ig";
connectAttr "skinCluster18GroupId.id" "skinCluster18.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster18.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster18.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster18.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster18.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster18.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster18.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster18.bp";
connectAttr "groupParts36.og" "tweak18.ip[0].ig";
connectAttr "groupId36.id" "tweak18.ip[0].gi";
connectAttr "skinCluster18GroupId.msg" "skinCluster18Set.gn" -na;
connectAttr "Joint_1_Object_24_SINGLEShape.iog.og[0]" "skinCluster18Set.dsm" -na
		;
connectAttr "skinCluster18.msg" "skinCluster18Set.ub[0]";
connectAttr "tweak18.og[0]" "skinCluster18GroupParts.ig";
connectAttr "skinCluster18GroupId.id" "skinCluster18GroupParts.gi";
connectAttr "groupId36.msg" "tweakSet18.gn" -na;
connectAttr "Joint_1_Object_24_SINGLEShape.iog.og[1]" "tweakSet18.dsm" -na;
connectAttr "tweak18.msg" "tweakSet18.ub[0]";
connectAttr "Joint_1_Object_24_SINGLEShapeOrig.w" "groupParts36.ig";
connectAttr "groupId36.id" "groupParts36.gi";
connectAttr "skinCluster19GroupParts.og" "skinCluster19.ip[0].ig";
connectAttr "skinCluster19GroupId.id" "skinCluster19.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster19.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster19.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster19.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster19.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster19.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster19.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster19.bp";
connectAttr "groupParts38.og" "tweak19.ip[0].ig";
connectAttr "groupId38.id" "tweak19.ip[0].gi";
connectAttr "skinCluster19GroupId.msg" "skinCluster19Set.gn" -na;
connectAttr "Joint_1_Object_25_SINGLEShape.iog.og[0]" "skinCluster19Set.dsm" -na
		;
connectAttr "skinCluster19.msg" "skinCluster19Set.ub[0]";
connectAttr "tweak19.og[0]" "skinCluster19GroupParts.ig";
connectAttr "skinCluster19GroupId.id" "skinCluster19GroupParts.gi";
connectAttr "groupId38.msg" "tweakSet19.gn" -na;
connectAttr "Joint_1_Object_25_SINGLEShape.iog.og[1]" "tweakSet19.dsm" -na;
connectAttr "tweak19.msg" "tweakSet19.ub[0]";
connectAttr "Joint_1_Object_25_SINGLEShapeOrig.w" "groupParts38.ig";
connectAttr "groupId38.id" "groupParts38.gi";
connectAttr "skinCluster20GroupParts.og" "skinCluster20.ip[0].ig";
connectAttr "skinCluster20GroupId.id" "skinCluster20.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster20.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster20.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster20.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster20.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster20.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster20.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster20.bp";
connectAttr "groupParts40.og" "tweak20.ip[0].ig";
connectAttr "groupId40.id" "tweak20.ip[0].gi";
connectAttr "skinCluster20GroupId.msg" "skinCluster20Set.gn" -na;
connectAttr "Joint_1_Object_26_SINGLEShape.iog.og[0]" "skinCluster20Set.dsm" -na
		;
connectAttr "skinCluster20.msg" "skinCluster20Set.ub[0]";
connectAttr "tweak20.og[0]" "skinCluster20GroupParts.ig";
connectAttr "skinCluster20GroupId.id" "skinCluster20GroupParts.gi";
connectAttr "groupId40.msg" "tweakSet20.gn" -na;
connectAttr "Joint_1_Object_26_SINGLEShape.iog.og[1]" "tweakSet20.dsm" -na;
connectAttr "tweak20.msg" "tweakSet20.ub[0]";
connectAttr "Joint_1_Object_26_SINGLEShapeOrig.w" "groupParts40.ig";
connectAttr "groupId40.id" "groupParts40.gi";
connectAttr "skinCluster21GroupParts.og" "skinCluster21.ip[0].ig";
connectAttr "skinCluster21GroupId.id" "skinCluster21.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster21.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster21.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster21.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster21.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster21.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster21.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster21.bp";
connectAttr "groupParts42.og" "tweak21.ip[0].ig";
connectAttr "groupId42.id" "tweak21.ip[0].gi";
connectAttr "skinCluster21GroupId.msg" "skinCluster21Set.gn" -na;
connectAttr "Joint_1_Object_27_SINGLEShape.iog.og[0]" "skinCluster21Set.dsm" -na
		;
connectAttr "skinCluster21.msg" "skinCluster21Set.ub[0]";
connectAttr "tweak21.og[0]" "skinCluster21GroupParts.ig";
connectAttr "skinCluster21GroupId.id" "skinCluster21GroupParts.gi";
connectAttr "groupId42.msg" "tweakSet21.gn" -na;
connectAttr "Joint_1_Object_27_SINGLEShape.iog.og[1]" "tweakSet21.dsm" -na;
connectAttr "tweak21.msg" "tweakSet21.ub[0]";
connectAttr "Joint_1_Object_27_SINGLEShapeOrig.w" "groupParts42.ig";
connectAttr "groupId42.id" "groupParts42.gi";
connectAttr "skinCluster22GroupParts.og" "skinCluster22.ip[0].ig";
connectAttr "skinCluster22GroupId.id" "skinCluster22.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster22.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster22.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster22.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster22.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster22.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster22.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster22.bp";
connectAttr "groupParts44.og" "tweak22.ip[0].ig";
connectAttr "groupId44.id" "tweak22.ip[0].gi";
connectAttr "skinCluster22GroupId.msg" "skinCluster22Set.gn" -na;
connectAttr "Joint_1_Object_28_SINGLEShape.iog.og[0]" "skinCluster22Set.dsm" -na
		;
connectAttr "skinCluster22.msg" "skinCluster22Set.ub[0]";
connectAttr "tweak22.og[0]" "skinCluster22GroupParts.ig";
connectAttr "skinCluster22GroupId.id" "skinCluster22GroupParts.gi";
connectAttr "groupId44.msg" "tweakSet22.gn" -na;
connectAttr "Joint_1_Object_28_SINGLEShape.iog.og[1]" "tweakSet22.dsm" -na;
connectAttr "tweak22.msg" "tweakSet22.ub[0]";
connectAttr "Joint_1_Object_28_SINGLEShapeOrig.w" "groupParts44.ig";
connectAttr "groupId44.id" "groupParts44.gi";
connectAttr "skinCluster23GroupParts.og" "skinCluster23.ip[0].ig";
connectAttr "skinCluster23GroupId.id" "skinCluster23.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster23.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster23.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster23.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster23.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster23.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster23.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster23.bp";
connectAttr "groupParts46.og" "tweak23.ip[0].ig";
connectAttr "groupId46.id" "tweak23.ip[0].gi";
connectAttr "skinCluster23GroupId.msg" "skinCluster23Set.gn" -na;
connectAttr "Joint_1_Object_29_SINGLEShape.iog.og[0]" "skinCluster23Set.dsm" -na
		;
connectAttr "skinCluster23.msg" "skinCluster23Set.ub[0]";
connectAttr "tweak23.og[0]" "skinCluster23GroupParts.ig";
connectAttr "skinCluster23GroupId.id" "skinCluster23GroupParts.gi";
connectAttr "groupId46.msg" "tweakSet23.gn" -na;
connectAttr "Joint_1_Object_29_SINGLEShape.iog.og[1]" "tweakSet23.dsm" -na;
connectAttr "tweak23.msg" "tweakSet23.ub[0]";
connectAttr "Joint_1_Object_29_SINGLEShapeOrig.w" "groupParts46.ig";
connectAttr "groupId46.id" "groupParts46.gi";
connectAttr "skinCluster24GroupParts.og" "skinCluster24.ip[0].ig";
connectAttr "skinCluster24GroupId.id" "skinCluster24.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster24.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster24.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster24.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster24.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster24.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster24.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster24.bp";
connectAttr "groupParts48.og" "tweak24.ip[0].ig";
connectAttr "groupId48.id" "tweak24.ip[0].gi";
connectAttr "skinCluster24GroupId.msg" "skinCluster24Set.gn" -na;
connectAttr "Joint_1_Object_3_SINGLEShape.iog.og[0]" "skinCluster24Set.dsm" -na;
connectAttr "skinCluster24.msg" "skinCluster24Set.ub[0]";
connectAttr "tweak24.og[0]" "skinCluster24GroupParts.ig";
connectAttr "skinCluster24GroupId.id" "skinCluster24GroupParts.gi";
connectAttr "groupId48.msg" "tweakSet24.gn" -na;
connectAttr "Joint_1_Object_3_SINGLEShape.iog.og[1]" "tweakSet24.dsm" -na;
connectAttr "tweak24.msg" "tweakSet24.ub[0]";
connectAttr "Joint_1_Object_3_SINGLEShapeOrig.w" "groupParts48.ig";
connectAttr "groupId48.id" "groupParts48.gi";
connectAttr "skinCluster25GroupParts.og" "skinCluster25.ip[0].ig";
connectAttr "skinCluster25GroupId.id" "skinCluster25.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster25.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster25.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster25.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster25.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster25.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster25.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster25.bp";
connectAttr "groupParts50.og" "tweak25.ip[0].ig";
connectAttr "groupId50.id" "tweak25.ip[0].gi";
connectAttr "skinCluster25GroupId.msg" "skinCluster25Set.gn" -na;
connectAttr "Joint_1_Object_30_SINGLEShape.iog.og[0]" "skinCluster25Set.dsm" -na
		;
connectAttr "skinCluster25.msg" "skinCluster25Set.ub[0]";
connectAttr "tweak25.og[0]" "skinCluster25GroupParts.ig";
connectAttr "skinCluster25GroupId.id" "skinCluster25GroupParts.gi";
connectAttr "groupId50.msg" "tweakSet25.gn" -na;
connectAttr "Joint_1_Object_30_SINGLEShape.iog.og[1]" "tweakSet25.dsm" -na;
connectAttr "tweak25.msg" "tweakSet25.ub[0]";
connectAttr "Joint_1_Object_30_SINGLEShapeOrig.w" "groupParts50.ig";
connectAttr "groupId50.id" "groupParts50.gi";
connectAttr "skinCluster26GroupParts.og" "skinCluster26.ip[0].ig";
connectAttr "skinCluster26GroupId.id" "skinCluster26.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster26.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster26.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster26.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster26.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster26.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster26.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster26.bp";
connectAttr "groupParts52.og" "tweak26.ip[0].ig";
connectAttr "groupId52.id" "tweak26.ip[0].gi";
connectAttr "skinCluster26GroupId.msg" "skinCluster26Set.gn" -na;
connectAttr "Joint_1_Object_31_SINGLEShape.iog.og[0]" "skinCluster26Set.dsm" -na
		;
connectAttr "skinCluster26.msg" "skinCluster26Set.ub[0]";
connectAttr "tweak26.og[0]" "skinCluster26GroupParts.ig";
connectAttr "skinCluster26GroupId.id" "skinCluster26GroupParts.gi";
connectAttr "groupId52.msg" "tweakSet26.gn" -na;
connectAttr "Joint_1_Object_31_SINGLEShape.iog.og[1]" "tweakSet26.dsm" -na;
connectAttr "tweak26.msg" "tweakSet26.ub[0]";
connectAttr "Joint_1_Object_31_SINGLEShapeOrig.w" "groupParts52.ig";
connectAttr "groupId52.id" "groupParts52.gi";
connectAttr "skinCluster27GroupParts.og" "skinCluster27.ip[0].ig";
connectAttr "skinCluster27GroupId.id" "skinCluster27.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster27.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster27.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster27.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster27.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster27.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster27.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster27.bp";
connectAttr "groupParts54.og" "tweak27.ip[0].ig";
connectAttr "groupId54.id" "tweak27.ip[0].gi";
connectAttr "skinCluster27GroupId.msg" "skinCluster27Set.gn" -na;
connectAttr "Joint_1_Object_32_SINGLEShape.iog.og[0]" "skinCluster27Set.dsm" -na
		;
connectAttr "skinCluster27.msg" "skinCluster27Set.ub[0]";
connectAttr "tweak27.og[0]" "skinCluster27GroupParts.ig";
connectAttr "skinCluster27GroupId.id" "skinCluster27GroupParts.gi";
connectAttr "groupId54.msg" "tweakSet27.gn" -na;
connectAttr "Joint_1_Object_32_SINGLEShape.iog.og[1]" "tweakSet27.dsm" -na;
connectAttr "tweak27.msg" "tweakSet27.ub[0]";
connectAttr "Joint_1_Object_32_SINGLEShapeOrig.w" "groupParts54.ig";
connectAttr "groupId54.id" "groupParts54.gi";
connectAttr "skinCluster28GroupParts.og" "skinCluster28.ip[0].ig";
connectAttr "skinCluster28GroupId.id" "skinCluster28.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster28.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster28.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster28.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster28.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster28.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster28.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster28.bp";
connectAttr "groupParts56.og" "tweak28.ip[0].ig";
connectAttr "groupId56.id" "tweak28.ip[0].gi";
connectAttr "skinCluster28GroupId.msg" "skinCluster28Set.gn" -na;
connectAttr "Joint_1_Object_33_SINGLEShape.iog.og[0]" "skinCluster28Set.dsm" -na
		;
connectAttr "skinCluster28.msg" "skinCluster28Set.ub[0]";
connectAttr "tweak28.og[0]" "skinCluster28GroupParts.ig";
connectAttr "skinCluster28GroupId.id" "skinCluster28GroupParts.gi";
connectAttr "groupId56.msg" "tweakSet28.gn" -na;
connectAttr "Joint_1_Object_33_SINGLEShape.iog.og[1]" "tweakSet28.dsm" -na;
connectAttr "tweak28.msg" "tweakSet28.ub[0]";
connectAttr "Joint_1_Object_33_SINGLEShapeOrig.w" "groupParts56.ig";
connectAttr "groupId56.id" "groupParts56.gi";
connectAttr "skinCluster29GroupParts.og" "skinCluster29.ip[0].ig";
connectAttr "skinCluster29GroupId.id" "skinCluster29.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster29.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster29.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster29.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster29.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster29.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster29.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster29.bp";
connectAttr "groupParts58.og" "tweak29.ip[0].ig";
connectAttr "groupId58.id" "tweak29.ip[0].gi";
connectAttr "skinCluster29GroupId.msg" "skinCluster29Set.gn" -na;
connectAttr "Joint_1_Object_34_SINGLEShape.iog.og[0]" "skinCluster29Set.dsm" -na
		;
connectAttr "skinCluster29.msg" "skinCluster29Set.ub[0]";
connectAttr "tweak29.og[0]" "skinCluster29GroupParts.ig";
connectAttr "skinCluster29GroupId.id" "skinCluster29GroupParts.gi";
connectAttr "groupId58.msg" "tweakSet29.gn" -na;
connectAttr "Joint_1_Object_34_SINGLEShape.iog.og[1]" "tweakSet29.dsm" -na;
connectAttr "tweak29.msg" "tweakSet29.ub[0]";
connectAttr "Joint_1_Object_34_SINGLEShapeOrig.w" "groupParts58.ig";
connectAttr "groupId58.id" "groupParts58.gi";
connectAttr "skinCluster30GroupParts.og" "skinCluster30.ip[0].ig";
connectAttr "skinCluster30GroupId.id" "skinCluster30.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster30.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster30.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster30.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster30.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster30.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster30.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster30.bp";
connectAttr "groupParts60.og" "tweak30.ip[0].ig";
connectAttr "groupId60.id" "tweak30.ip[0].gi";
connectAttr "skinCluster30GroupId.msg" "skinCluster30Set.gn" -na;
connectAttr "Joint_1_Object_35_SINGLEShape.iog.og[0]" "skinCluster30Set.dsm" -na
		;
connectAttr "skinCluster30.msg" "skinCluster30Set.ub[0]";
connectAttr "tweak30.og[0]" "skinCluster30GroupParts.ig";
connectAttr "skinCluster30GroupId.id" "skinCluster30GroupParts.gi";
connectAttr "groupId60.msg" "tweakSet30.gn" -na;
connectAttr "Joint_1_Object_35_SINGLEShape.iog.og[1]" "tweakSet30.dsm" -na;
connectAttr "tweak30.msg" "tweakSet30.ub[0]";
connectAttr "Joint_1_Object_35_SINGLEShapeOrig.w" "groupParts60.ig";
connectAttr "groupId60.id" "groupParts60.gi";
connectAttr "skinCluster31GroupParts.og" "skinCluster31.ip[0].ig";
connectAttr "skinCluster31GroupId.id" "skinCluster31.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster31.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster31.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster31.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster31.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster31.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster31.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster31.bp";
connectAttr "groupParts62.og" "tweak31.ip[0].ig";
connectAttr "groupId62.id" "tweak31.ip[0].gi";
connectAttr "skinCluster31GroupId.msg" "skinCluster31Set.gn" -na;
connectAttr "Joint_1_Object_36_SINGLEShape.iog.og[0]" "skinCluster31Set.dsm" -na
		;
connectAttr "skinCluster31.msg" "skinCluster31Set.ub[0]";
connectAttr "tweak31.og[0]" "skinCluster31GroupParts.ig";
connectAttr "skinCluster31GroupId.id" "skinCluster31GroupParts.gi";
connectAttr "groupId62.msg" "tweakSet31.gn" -na;
connectAttr "Joint_1_Object_36_SINGLEShape.iog.og[1]" "tweakSet31.dsm" -na;
connectAttr "tweak31.msg" "tweakSet31.ub[0]";
connectAttr "Joint_1_Object_36_SINGLEShapeOrig.w" "groupParts62.ig";
connectAttr "groupId62.id" "groupParts62.gi";
connectAttr "skinCluster32GroupParts.og" "skinCluster32.ip[0].ig";
connectAttr "skinCluster32GroupId.id" "skinCluster32.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster32.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster32.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster32.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster32.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster32.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster32.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster32.bp";
connectAttr "groupParts64.og" "tweak32.ip[0].ig";
connectAttr "groupId64.id" "tweak32.ip[0].gi";
connectAttr "skinCluster32GroupId.msg" "skinCluster32Set.gn" -na;
connectAttr "Joint_1_Object_37_SINGLEShape.iog.og[0]" "skinCluster32Set.dsm" -na
		;
connectAttr "skinCluster32.msg" "skinCluster32Set.ub[0]";
connectAttr "tweak32.og[0]" "skinCluster32GroupParts.ig";
connectAttr "skinCluster32GroupId.id" "skinCluster32GroupParts.gi";
connectAttr "groupId64.msg" "tweakSet32.gn" -na;
connectAttr "Joint_1_Object_37_SINGLEShape.iog.og[1]" "tweakSet32.dsm" -na;
connectAttr "tweak32.msg" "tweakSet32.ub[0]";
connectAttr "Joint_1_Object_37_SINGLEShapeOrig.w" "groupParts64.ig";
connectAttr "groupId64.id" "groupParts64.gi";
connectAttr "skinCluster33GroupParts.og" "skinCluster33.ip[0].ig";
connectAttr "skinCluster33GroupId.id" "skinCluster33.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster33.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster33.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster33.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster33.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster33.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster33.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster33.bp";
connectAttr "groupParts66.og" "tweak33.ip[0].ig";
connectAttr "groupId66.id" "tweak33.ip[0].gi";
connectAttr "skinCluster33GroupId.msg" "skinCluster33Set.gn" -na;
connectAttr "Joint_1_Object_38_SINGLEShape.iog.og[0]" "skinCluster33Set.dsm" -na
		;
connectAttr "skinCluster33.msg" "skinCluster33Set.ub[0]";
connectAttr "tweak33.og[0]" "skinCluster33GroupParts.ig";
connectAttr "skinCluster33GroupId.id" "skinCluster33GroupParts.gi";
connectAttr "groupId66.msg" "tweakSet33.gn" -na;
connectAttr "Joint_1_Object_38_SINGLEShape.iog.og[1]" "tweakSet33.dsm" -na;
connectAttr "tweak33.msg" "tweakSet33.ub[0]";
connectAttr "Joint_1_Object_38_SINGLEShapeOrig.w" "groupParts66.ig";
connectAttr "groupId66.id" "groupParts66.gi";
connectAttr "skinCluster34GroupParts.og" "skinCluster34.ip[0].ig";
connectAttr "skinCluster34GroupId.id" "skinCluster34.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster34.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster34.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster34.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster34.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster34.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster34.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster34.bp";
connectAttr "groupParts68.og" "tweak34.ip[0].ig";
connectAttr "groupId68.id" "tweak34.ip[0].gi";
connectAttr "skinCluster34GroupId.msg" "skinCluster34Set.gn" -na;
connectAttr "Joint_1_Object_39_SINGLEShape.iog.og[0]" "skinCluster34Set.dsm" -na
		;
connectAttr "skinCluster34.msg" "skinCluster34Set.ub[0]";
connectAttr "tweak34.og[0]" "skinCluster34GroupParts.ig";
connectAttr "skinCluster34GroupId.id" "skinCluster34GroupParts.gi";
connectAttr "groupId68.msg" "tweakSet34.gn" -na;
connectAttr "Joint_1_Object_39_SINGLEShape.iog.og[1]" "tweakSet34.dsm" -na;
connectAttr "tweak34.msg" "tweakSet34.ub[0]";
connectAttr "Joint_1_Object_39_SINGLEShapeOrig.w" "groupParts68.ig";
connectAttr "groupId68.id" "groupParts68.gi";
connectAttr "skinCluster35GroupParts.og" "skinCluster35.ip[0].ig";
connectAttr "skinCluster35GroupId.id" "skinCluster35.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster35.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster35.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster35.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster35.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster35.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster35.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster35.bp";
connectAttr "groupParts70.og" "tweak35.ip[0].ig";
connectAttr "groupId70.id" "tweak35.ip[0].gi";
connectAttr "skinCluster35GroupId.msg" "skinCluster35Set.gn" -na;
connectAttr "Joint_1_Object_4_SINGLEShape.iog.og[0]" "skinCluster35Set.dsm" -na;
connectAttr "skinCluster35.msg" "skinCluster35Set.ub[0]";
connectAttr "tweak35.og[0]" "skinCluster35GroupParts.ig";
connectAttr "skinCluster35GroupId.id" "skinCluster35GroupParts.gi";
connectAttr "groupId70.msg" "tweakSet35.gn" -na;
connectAttr "Joint_1_Object_4_SINGLEShape.iog.og[1]" "tweakSet35.dsm" -na;
connectAttr "tweak35.msg" "tweakSet35.ub[0]";
connectAttr "Joint_1_Object_4_SINGLEShapeOrig.w" "groupParts70.ig";
connectAttr "groupId70.id" "groupParts70.gi";
connectAttr "skinCluster36GroupParts.og" "skinCluster36.ip[0].ig";
connectAttr "skinCluster36GroupId.id" "skinCluster36.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster36.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster36.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster36.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster36.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster36.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster36.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster36.bp";
connectAttr "groupParts72.og" "tweak36.ip[0].ig";
connectAttr "groupId72.id" "tweak36.ip[0].gi";
connectAttr "skinCluster36GroupId.msg" "skinCluster36Set.gn" -na;
connectAttr "Joint_1_Object_40_SINGLEShape.iog.og[0]" "skinCluster36Set.dsm" -na
		;
connectAttr "skinCluster36.msg" "skinCluster36Set.ub[0]";
connectAttr "tweak36.og[0]" "skinCluster36GroupParts.ig";
connectAttr "skinCluster36GroupId.id" "skinCluster36GroupParts.gi";
connectAttr "groupId72.msg" "tweakSet36.gn" -na;
connectAttr "Joint_1_Object_40_SINGLEShape.iog.og[1]" "tweakSet36.dsm" -na;
connectAttr "tweak36.msg" "tweakSet36.ub[0]";
connectAttr "Joint_1_Object_40_SINGLEShapeOrig.w" "groupParts72.ig";
connectAttr "groupId72.id" "groupParts72.gi";
connectAttr "skinCluster37GroupParts.og" "skinCluster37.ip[0].ig";
connectAttr "skinCluster37GroupId.id" "skinCluster37.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster37.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster37.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster37.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster37.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster37.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster37.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster37.bp";
connectAttr "groupParts74.og" "tweak37.ip[0].ig";
connectAttr "groupId74.id" "tweak37.ip[0].gi";
connectAttr "skinCluster37GroupId.msg" "skinCluster37Set.gn" -na;
connectAttr "Joint_1_Object_41_SINGLEShape.iog.og[0]" "skinCluster37Set.dsm" -na
		;
connectAttr "skinCluster37.msg" "skinCluster37Set.ub[0]";
connectAttr "tweak37.og[0]" "skinCluster37GroupParts.ig";
connectAttr "skinCluster37GroupId.id" "skinCluster37GroupParts.gi";
connectAttr "groupId74.msg" "tweakSet37.gn" -na;
connectAttr "Joint_1_Object_41_SINGLEShape.iog.og[1]" "tweakSet37.dsm" -na;
connectAttr "tweak37.msg" "tweakSet37.ub[0]";
connectAttr "Joint_1_Object_41_SINGLEShapeOrig.w" "groupParts74.ig";
connectAttr "groupId74.id" "groupParts74.gi";
connectAttr "skinCluster38GroupParts.og" "skinCluster38.ip[0].ig";
connectAttr "skinCluster38GroupId.id" "skinCluster38.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster38.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster38.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster38.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster38.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster38.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster38.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster38.bp";
connectAttr "groupParts76.og" "tweak38.ip[0].ig";
connectAttr "groupId76.id" "tweak38.ip[0].gi";
connectAttr "skinCluster38GroupId.msg" "skinCluster38Set.gn" -na;
connectAttr "Joint_1_Object_42_SINGLEShape.iog.og[0]" "skinCluster38Set.dsm" -na
		;
connectAttr "skinCluster38.msg" "skinCluster38Set.ub[0]";
connectAttr "tweak38.og[0]" "skinCluster38GroupParts.ig";
connectAttr "skinCluster38GroupId.id" "skinCluster38GroupParts.gi";
connectAttr "groupId76.msg" "tweakSet38.gn" -na;
connectAttr "Joint_1_Object_42_SINGLEShape.iog.og[1]" "tweakSet38.dsm" -na;
connectAttr "tweak38.msg" "tweakSet38.ub[0]";
connectAttr "Joint_1_Object_42_SINGLEShapeOrig.w" "groupParts76.ig";
connectAttr "groupId76.id" "groupParts76.gi";
connectAttr "skinCluster39GroupParts.og" "skinCluster39.ip[0].ig";
connectAttr "skinCluster39GroupId.id" "skinCluster39.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster39.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster39.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster39.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster39.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster39.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster39.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster39.bp";
connectAttr "groupParts78.og" "tweak39.ip[0].ig";
connectAttr "groupId78.id" "tweak39.ip[0].gi";
connectAttr "skinCluster39GroupId.msg" "skinCluster39Set.gn" -na;
connectAttr "Joint_1_Object_43_SINGLEShape.iog.og[0]" "skinCluster39Set.dsm" -na
		;
connectAttr "skinCluster39.msg" "skinCluster39Set.ub[0]";
connectAttr "tweak39.og[0]" "skinCluster39GroupParts.ig";
connectAttr "skinCluster39GroupId.id" "skinCluster39GroupParts.gi";
connectAttr "groupId78.msg" "tweakSet39.gn" -na;
connectAttr "Joint_1_Object_43_SINGLEShape.iog.og[1]" "tweakSet39.dsm" -na;
connectAttr "tweak39.msg" "tweakSet39.ub[0]";
connectAttr "Joint_1_Object_43_SINGLEShapeOrig.w" "groupParts78.ig";
connectAttr "groupId78.id" "groupParts78.gi";
connectAttr "skinCluster40GroupParts.og" "skinCluster40.ip[0].ig";
connectAttr "skinCluster40GroupId.id" "skinCluster40.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster40.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster40.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster40.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster40.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster40.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster40.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster40.bp";
connectAttr "groupParts80.og" "tweak40.ip[0].ig";
connectAttr "groupId80.id" "tweak40.ip[0].gi";
connectAttr "skinCluster40GroupId.msg" "skinCluster40Set.gn" -na;
connectAttr "Joint_1_Object_44_SINGLEShape.iog.og[0]" "skinCluster40Set.dsm" -na
		;
connectAttr "skinCluster40.msg" "skinCluster40Set.ub[0]";
connectAttr "tweak40.og[0]" "skinCluster40GroupParts.ig";
connectAttr "skinCluster40GroupId.id" "skinCluster40GroupParts.gi";
connectAttr "groupId80.msg" "tweakSet40.gn" -na;
connectAttr "Joint_1_Object_44_SINGLEShape.iog.og[1]" "tweakSet40.dsm" -na;
connectAttr "tweak40.msg" "tweakSet40.ub[0]";
connectAttr "Joint_1_Object_44_SINGLEShapeOrig.w" "groupParts80.ig";
connectAttr "groupId80.id" "groupParts80.gi";
connectAttr "skinCluster41GroupParts.og" "skinCluster41.ip[0].ig";
connectAttr "skinCluster41GroupId.id" "skinCluster41.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster41.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster41.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster41.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster41.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster41.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster41.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster41.bp";
connectAttr "groupParts82.og" "tweak41.ip[0].ig";
connectAttr "groupId82.id" "tweak41.ip[0].gi";
connectAttr "skinCluster41GroupId.msg" "skinCluster41Set.gn" -na;
connectAttr "Joint_1_Object_45_SINGLEShape.iog.og[0]" "skinCluster41Set.dsm" -na
		;
connectAttr "skinCluster41.msg" "skinCluster41Set.ub[0]";
connectAttr "tweak41.og[0]" "skinCluster41GroupParts.ig";
connectAttr "skinCluster41GroupId.id" "skinCluster41GroupParts.gi";
connectAttr "groupId82.msg" "tweakSet41.gn" -na;
connectAttr "Joint_1_Object_45_SINGLEShape.iog.og[1]" "tweakSet41.dsm" -na;
connectAttr "tweak41.msg" "tweakSet41.ub[0]";
connectAttr "Joint_1_Object_45_SINGLEShapeOrig.w" "groupParts82.ig";
connectAttr "groupId82.id" "groupParts82.gi";
connectAttr "skinCluster42GroupParts.og" "skinCluster42.ip[0].ig";
connectAttr "skinCluster42GroupId.id" "skinCluster42.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster42.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster42.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster42.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster42.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster42.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster42.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster42.bp";
connectAttr "groupParts84.og" "tweak42.ip[0].ig";
connectAttr "groupId84.id" "tweak42.ip[0].gi";
connectAttr "skinCluster42GroupId.msg" "skinCluster42Set.gn" -na;
connectAttr "Joint_1_Object_46_SINGLEShape.iog.og[0]" "skinCluster42Set.dsm" -na
		;
connectAttr "skinCluster42.msg" "skinCluster42Set.ub[0]";
connectAttr "tweak42.og[0]" "skinCluster42GroupParts.ig";
connectAttr "skinCluster42GroupId.id" "skinCluster42GroupParts.gi";
connectAttr "groupId84.msg" "tweakSet42.gn" -na;
connectAttr "Joint_1_Object_46_SINGLEShape.iog.og[1]" "tweakSet42.dsm" -na;
connectAttr "tweak42.msg" "tweakSet42.ub[0]";
connectAttr "Joint_1_Object_46_SINGLEShapeOrig.w" "groupParts84.ig";
connectAttr "groupId84.id" "groupParts84.gi";
connectAttr "skinCluster43GroupParts.og" "skinCluster43.ip[0].ig";
connectAttr "skinCluster43GroupId.id" "skinCluster43.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster43.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster43.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster43.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster43.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster43.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster43.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster43.bp";
connectAttr "groupParts86.og" "tweak43.ip[0].ig";
connectAttr "groupId86.id" "tweak43.ip[0].gi";
connectAttr "skinCluster43GroupId.msg" "skinCluster43Set.gn" -na;
connectAttr "Joint_1_Object_47_SINGLEShape.iog.og[0]" "skinCluster43Set.dsm" -na
		;
connectAttr "skinCluster43.msg" "skinCluster43Set.ub[0]";
connectAttr "tweak43.og[0]" "skinCluster43GroupParts.ig";
connectAttr "skinCluster43GroupId.id" "skinCluster43GroupParts.gi";
connectAttr "groupId86.msg" "tweakSet43.gn" -na;
connectAttr "Joint_1_Object_47_SINGLEShape.iog.og[1]" "tweakSet43.dsm" -na;
connectAttr "tweak43.msg" "tweakSet43.ub[0]";
connectAttr "Joint_1_Object_47_SINGLEShapeOrig.w" "groupParts86.ig";
connectAttr "groupId86.id" "groupParts86.gi";
connectAttr "skinCluster44GroupParts.og" "skinCluster44.ip[0].ig";
connectAttr "skinCluster44GroupId.id" "skinCluster44.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster44.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster44.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster44.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster44.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster44.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster44.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster44.bp";
connectAttr "groupParts88.og" "tweak44.ip[0].ig";
connectAttr "groupId88.id" "tweak44.ip[0].gi";
connectAttr "skinCluster44GroupId.msg" "skinCluster44Set.gn" -na;
connectAttr "Joint_1_Object_48_SINGLEShape.iog.og[0]" "skinCluster44Set.dsm" -na
		;
connectAttr "skinCluster44.msg" "skinCluster44Set.ub[0]";
connectAttr "tweak44.og[0]" "skinCluster44GroupParts.ig";
connectAttr "skinCluster44GroupId.id" "skinCluster44GroupParts.gi";
connectAttr "groupId88.msg" "tweakSet44.gn" -na;
connectAttr "Joint_1_Object_48_SINGLEShape.iog.og[1]" "tweakSet44.dsm" -na;
connectAttr "tweak44.msg" "tweakSet44.ub[0]";
connectAttr "Joint_1_Object_48_SINGLEShapeOrig.w" "groupParts88.ig";
connectAttr "groupId88.id" "groupParts88.gi";
connectAttr "skinCluster45GroupParts.og" "skinCluster45.ip[0].ig";
connectAttr "skinCluster45GroupId.id" "skinCluster45.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster45.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster45.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster45.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster45.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster45.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster45.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster45.bp";
connectAttr "groupParts90.og" "tweak45.ip[0].ig";
connectAttr "groupId90.id" "tweak45.ip[0].gi";
connectAttr "skinCluster45GroupId.msg" "skinCluster45Set.gn" -na;
connectAttr "Joint_1_Object_49_SINGLEShape.iog.og[0]" "skinCluster45Set.dsm" -na
		;
connectAttr "skinCluster45.msg" "skinCluster45Set.ub[0]";
connectAttr "tweak45.og[0]" "skinCluster45GroupParts.ig";
connectAttr "skinCluster45GroupId.id" "skinCluster45GroupParts.gi";
connectAttr "groupId90.msg" "tweakSet45.gn" -na;
connectAttr "Joint_1_Object_49_SINGLEShape.iog.og[1]" "tweakSet45.dsm" -na;
connectAttr "tweak45.msg" "tweakSet45.ub[0]";
connectAttr "Joint_1_Object_49_SINGLEShapeOrig.w" "groupParts90.ig";
connectAttr "groupId90.id" "groupParts90.gi";
connectAttr "skinCluster46GroupParts.og" "skinCluster46.ip[0].ig";
connectAttr "skinCluster46GroupId.id" "skinCluster46.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster46.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster46.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster46.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster46.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster46.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster46.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster46.bp";
connectAttr "groupParts92.og" "tweak46.ip[0].ig";
connectAttr "groupId92.id" "tweak46.ip[0].gi";
connectAttr "skinCluster46GroupId.msg" "skinCluster46Set.gn" -na;
connectAttr "Joint_1_Object_5_SINGLEShape.iog.og[0]" "skinCluster46Set.dsm" -na;
connectAttr "skinCluster46.msg" "skinCluster46Set.ub[0]";
connectAttr "tweak46.og[0]" "skinCluster46GroupParts.ig";
connectAttr "skinCluster46GroupId.id" "skinCluster46GroupParts.gi";
connectAttr "groupId92.msg" "tweakSet46.gn" -na;
connectAttr "Joint_1_Object_5_SINGLEShape.iog.og[1]" "tweakSet46.dsm" -na;
connectAttr "tweak46.msg" "tweakSet46.ub[0]";
connectAttr "Joint_1_Object_5_SINGLEShapeOrig.w" "groupParts92.ig";
connectAttr "groupId92.id" "groupParts92.gi";
connectAttr "skinCluster47GroupParts.og" "skinCluster47.ip[0].ig";
connectAttr "skinCluster47GroupId.id" "skinCluster47.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster47.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster47.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster47.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster47.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster47.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster47.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster47.bp";
connectAttr "groupParts94.og" "tweak47.ip[0].ig";
connectAttr "groupId94.id" "tweak47.ip[0].gi";
connectAttr "skinCluster47GroupId.msg" "skinCluster47Set.gn" -na;
connectAttr "Joint_1_Object_50_SINGLEShape.iog.og[0]" "skinCluster47Set.dsm" -na
		;
connectAttr "skinCluster47.msg" "skinCluster47Set.ub[0]";
connectAttr "tweak47.og[0]" "skinCluster47GroupParts.ig";
connectAttr "skinCluster47GroupId.id" "skinCluster47GroupParts.gi";
connectAttr "groupId94.msg" "tweakSet47.gn" -na;
connectAttr "Joint_1_Object_50_SINGLEShape.iog.og[1]" "tweakSet47.dsm" -na;
connectAttr "tweak47.msg" "tweakSet47.ub[0]";
connectAttr "Joint_1_Object_50_SINGLEShapeOrig.w" "groupParts94.ig";
connectAttr "groupId94.id" "groupParts94.gi";
connectAttr "skinCluster48GroupParts.og" "skinCluster48.ip[0].ig";
connectAttr "skinCluster48GroupId.id" "skinCluster48.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster48.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster48.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster48.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster48.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster48.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster48.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster48.bp";
connectAttr "groupParts96.og" "tweak48.ip[0].ig";
connectAttr "groupId96.id" "tweak48.ip[0].gi";
connectAttr "skinCluster48GroupId.msg" "skinCluster48Set.gn" -na;
connectAttr "Joint_1_Object_51_SINGLEShape.iog.og[0]" "skinCluster48Set.dsm" -na
		;
connectAttr "skinCluster48.msg" "skinCluster48Set.ub[0]";
connectAttr "tweak48.og[0]" "skinCluster48GroupParts.ig";
connectAttr "skinCluster48GroupId.id" "skinCluster48GroupParts.gi";
connectAttr "groupId96.msg" "tweakSet48.gn" -na;
connectAttr "Joint_1_Object_51_SINGLEShape.iog.og[1]" "tweakSet48.dsm" -na;
connectAttr "tweak48.msg" "tweakSet48.ub[0]";
connectAttr "Joint_1_Object_51_SINGLEShapeOrig.w" "groupParts96.ig";
connectAttr "groupId96.id" "groupParts96.gi";
connectAttr "skinCluster49GroupParts.og" "skinCluster49.ip[0].ig";
connectAttr "skinCluster49GroupId.id" "skinCluster49.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster49.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster49.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster49.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster49.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster49.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster49.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster49.bp";
connectAttr "groupParts98.og" "tweak49.ip[0].ig";
connectAttr "groupId98.id" "tweak49.ip[0].gi";
connectAttr "skinCluster49GroupId.msg" "skinCluster49Set.gn" -na;
connectAttr "Joint_1_Object_52_SINGLEShape.iog.og[0]" "skinCluster49Set.dsm" -na
		;
connectAttr "skinCluster49.msg" "skinCluster49Set.ub[0]";
connectAttr "tweak49.og[0]" "skinCluster49GroupParts.ig";
connectAttr "skinCluster49GroupId.id" "skinCluster49GroupParts.gi";
connectAttr "groupId98.msg" "tweakSet49.gn" -na;
connectAttr "Joint_1_Object_52_SINGLEShape.iog.og[1]" "tweakSet49.dsm" -na;
connectAttr "tweak49.msg" "tweakSet49.ub[0]";
connectAttr "Joint_1_Object_52_SINGLEShapeOrig.w" "groupParts98.ig";
connectAttr "groupId98.id" "groupParts98.gi";
connectAttr "skinCluster50GroupParts.og" "skinCluster50.ip[0].ig";
connectAttr "skinCluster50GroupId.id" "skinCluster50.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster50.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster50.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster50.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster50.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster50.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster50.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster50.bp";
connectAttr "groupParts100.og" "tweak50.ip[0].ig";
connectAttr "groupId100.id" "tweak50.ip[0].gi";
connectAttr "skinCluster50GroupId.msg" "skinCluster50Set.gn" -na;
connectAttr "Joint_1_Object_53_SINGLEShape.iog.og[0]" "skinCluster50Set.dsm" -na
		;
connectAttr "skinCluster50.msg" "skinCluster50Set.ub[0]";
connectAttr "tweak50.og[0]" "skinCluster50GroupParts.ig";
connectAttr "skinCluster50GroupId.id" "skinCluster50GroupParts.gi";
connectAttr "groupId100.msg" "tweakSet50.gn" -na;
connectAttr "Joint_1_Object_53_SINGLEShape.iog.og[1]" "tweakSet50.dsm" -na;
connectAttr "tweak50.msg" "tweakSet50.ub[0]";
connectAttr "Joint_1_Object_53_SINGLEShapeOrig.w" "groupParts100.ig";
connectAttr "groupId100.id" "groupParts100.gi";
connectAttr "skinCluster51GroupParts.og" "skinCluster51.ip[0].ig";
connectAttr "skinCluster51GroupId.id" "skinCluster51.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster51.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster51.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster51.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster51.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster51.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster51.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster51.bp";
connectAttr "groupParts102.og" "tweak51.ip[0].ig";
connectAttr "groupId102.id" "tweak51.ip[0].gi";
connectAttr "skinCluster51GroupId.msg" "skinCluster51Set.gn" -na;
connectAttr "Joint_1_Object_6_SINGLEShape.iog.og[0]" "skinCluster51Set.dsm" -na;
connectAttr "skinCluster51.msg" "skinCluster51Set.ub[0]";
connectAttr "tweak51.og[0]" "skinCluster51GroupParts.ig";
connectAttr "skinCluster51GroupId.id" "skinCluster51GroupParts.gi";
connectAttr "groupId102.msg" "tweakSet51.gn" -na;
connectAttr "Joint_1_Object_6_SINGLEShape.iog.og[1]" "tweakSet51.dsm" -na;
connectAttr "tweak51.msg" "tweakSet51.ub[0]";
connectAttr "Joint_1_Object_6_SINGLEShapeOrig.w" "groupParts102.ig";
connectAttr "groupId102.id" "groupParts102.gi";
connectAttr "skinCluster52GroupParts.og" "skinCluster52.ip[0].ig";
connectAttr "skinCluster52GroupId.id" "skinCluster52.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster52.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster52.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster52.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster52.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster52.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster52.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster52.bp";
connectAttr "groupParts104.og" "tweak52.ip[0].ig";
connectAttr "groupId104.id" "tweak52.ip[0].gi";
connectAttr "skinCluster52GroupId.msg" "skinCluster52Set.gn" -na;
connectAttr "Joint_1_Object_7_SINGLEShape.iog.og[0]" "skinCluster52Set.dsm" -na;
connectAttr "skinCluster52.msg" "skinCluster52Set.ub[0]";
connectAttr "tweak52.og[0]" "skinCluster52GroupParts.ig";
connectAttr "skinCluster52GroupId.id" "skinCluster52GroupParts.gi";
connectAttr "groupId104.msg" "tweakSet52.gn" -na;
connectAttr "Joint_1_Object_7_SINGLEShape.iog.og[1]" "tweakSet52.dsm" -na;
connectAttr "tweak52.msg" "tweakSet52.ub[0]";
connectAttr "Joint_1_Object_7_SINGLEShapeOrig.w" "groupParts104.ig";
connectAttr "groupId104.id" "groupParts104.gi";
connectAttr "skinCluster53GroupParts.og" "skinCluster53.ip[0].ig";
connectAttr "skinCluster53GroupId.id" "skinCluster53.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster53.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster53.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster53.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster53.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster53.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster53.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster53.bp";
connectAttr "groupParts106.og" "tweak53.ip[0].ig";
connectAttr "groupId106.id" "tweak53.ip[0].gi";
connectAttr "skinCluster53GroupId.msg" "skinCluster53Set.gn" -na;
connectAttr "Joint_1_Object_8_SINGLEShape.iog.og[0]" "skinCluster53Set.dsm" -na;
connectAttr "skinCluster53.msg" "skinCluster53Set.ub[0]";
connectAttr "tweak53.og[0]" "skinCluster53GroupParts.ig";
connectAttr "skinCluster53GroupId.id" "skinCluster53GroupParts.gi";
connectAttr "groupId106.msg" "tweakSet53.gn" -na;
connectAttr "Joint_1_Object_8_SINGLEShape.iog.og[1]" "tweakSet53.dsm" -na;
connectAttr "tweak53.msg" "tweakSet53.ub[0]";
connectAttr "Joint_1_Object_8_SINGLEShapeOrig.w" "groupParts106.ig";
connectAttr "groupId106.id" "groupParts106.gi";
connectAttr "skinCluster54GroupParts.og" "skinCluster54.ip[0].ig";
connectAttr "skinCluster54GroupId.id" "skinCluster54.ip[0].gi";
connectAttr "JOBJ_1.wm" "skinCluster54.ma[0]";
connectAttr "JOBJ_0.wm" "skinCluster54.ma[1]";
connectAttr "JOBJ_1.liw" "skinCluster54.lw[0]";
connectAttr "JOBJ_0.liw" "skinCluster54.lw[1]";
connectAttr "JOBJ_1.obcc" "skinCluster54.ifcl[0]";
connectAttr "JOBJ_0.obcc" "skinCluster54.ifcl[1]";
connectAttr "bindPose1.msg" "skinCluster54.bp";
connectAttr "groupParts108.og" "tweak54.ip[0].ig";
connectAttr "groupId108.id" "tweak54.ip[0].gi";
connectAttr "skinCluster54GroupId.msg" "skinCluster54Set.gn" -na;
connectAttr "Joint_1_Object_9_SINGLEShape.iog.og[0]" "skinCluster54Set.dsm" -na;
connectAttr "skinCluster54.msg" "skinCluster54Set.ub[0]";
connectAttr "tweak54.og[0]" "skinCluster54GroupParts.ig";
connectAttr "skinCluster54GroupId.id" "skinCluster54GroupParts.gi";
connectAttr "groupId108.msg" "tweakSet54.gn" -na;
connectAttr "Joint_1_Object_9_SINGLEShape.iog.og[1]" "tweakSet54.dsm" -na;
connectAttr "tweak54.msg" "tweakSet54.ub[0]";
connectAttr "Joint_1_Object_9_SINGLEShapeOrig.w" "groupParts108.ig";
connectAttr "groupId108.id" "groupParts108.gi";
connectAttr "Joint_1_Object_0_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_1_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_2_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_3_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_4_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_5_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_6_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_7_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_8_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_9_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_10_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_11_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_12_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_13_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_14_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_15_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_16_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_17_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_18_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_19_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_20_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_21_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_22_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_23_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_24_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_25_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_26_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_27_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_28_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_29_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_30_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_31_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_32_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_33_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_34_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_35_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_36_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_37_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_38_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_39_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_40_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_41_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_42_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_43_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_44_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_45_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_46_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_47_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_48_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_49_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_50_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_51_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_52_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_53_SINGLESG.pa" ":renderPartition.st" -na;
connectAttr "Joint_1_Object_0_Material_0.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_1_Material_1.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_2_Material_2.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_3_Material_3.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_4_Material_4.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_5_Material_5.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_6_Material_6.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_7_Material_7.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_8_Material_8.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_9_Material_9.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_10_Material_10.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_11_Material_11.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_12_Material_12.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_13_Material_13.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_14_Material_14.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_15_Material_15.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_16_Material_16.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_17_Material_17.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_18_Material_18.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_19_Material_19.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_20_Material_20.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_21_Material_21.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_22_Material_22.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_23_Material_23.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_24_Material_24.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_25_Material_25.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_26_Material_26.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_27_Material_27.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_28_Material_28.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_29_Material_29.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_30_Material_30.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_31_Material_31.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_32_Material_32.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_33_Material_33.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_34_Material_34.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_35_Material_35.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_36_Material_36.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_37_Material_37.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_38_Material_38.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_39_Material_39.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_40_Material_40.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_41_Material_41.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_42_Material_42.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_43_Material_43.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_44_Material_44.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_45_Material_45.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_46_Material_46.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_47_Material_47.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_48_Material_48.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_49_Material_49.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_50_Material_50.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_51_Material_51.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_52_Material_52.msg" ":defaultShaderList1.s" -na;
connectAttr "Joint_1_Object_53_Material_53.msg" ":defaultShaderList1.s" -na;
connectAttr "place2dTexture1.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture2.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture3.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture4.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture5.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture6.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture7.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture8.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture9.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture10.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture11.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture12.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture13.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture14.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture15.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture16.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture17.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture18.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture19.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture20.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture21.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture22.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture23.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture24.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture25.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture26.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture27.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture28.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture29.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture30.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture31.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture32.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture33.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture34.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture35.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture36.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture37.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture38.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture39.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture40.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture41.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture42.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture43.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture44.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture45.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture46.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture47.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture48.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture49.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture50.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture51.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture52.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture53.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "place2dTexture54.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "defaultRenderLayer.msg" ":defaultRenderingList1.r" -na;
connectAttr "Image.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image1.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image2.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image3.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image4.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image5.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image6.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image7.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image8.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image9.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image10.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image11.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image12.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image13.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image14.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image15.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image16.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image17.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image18.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image19.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image20.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image21.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image22.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image23.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image24.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image25.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image26.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image27.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image28.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image29.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image30.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image31.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image32.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image33.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image34.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image35.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image36.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image37.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image38.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image39.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image40.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image41.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image42.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image43.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image44.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image45.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image46.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image47.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image48.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image49.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image50.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image51.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image52.msg" ":defaultTextureList1.tx" -na;
connectAttr "Image53.msg" ":defaultTextureList1.tx" -na;
// End of Wolfen.ma
