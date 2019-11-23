#!/usr/bin/env python3
import os;
import subprocess as sp;
import shutil;
import filecmp;

if(os.environ['TRAVIS_BRANCH'] == 'master' and os.environ['TRAVIS_PULL_REQUEST'] == 'false'):
    SQR = 'sonarqube-repair';
    branch = 'SonarqubeRepair';
    sourceFolder = SQR + '/source/act/original';
    rules = ['2111', '2116', '2272', '4973'];
    # Clone SQ-Repair and package it
    # Need to use my fork which has normal mode specified
    sp.call(['git', 'clone', 'git@github.com:HarisAdzemovic/' + SQR + '.git']);
    sp.call(['mvn', 'clean', 'package'], cwd = SQR);
    sp.call(['git', 'checkout', '-b', branch]);
    # Find all java files in the project to be analyzed
    originalFiles = [];
    for r, d, f in os.walk('src'):
        for file in f:
            if '.java' in file:
                originalFiles.append(os.path.join(r, file))

    # Create a directory in SQ-repair to hold the originals
    try:
        shutil.rmtree(sourceFolder, ignore_errors=True);
    except OSError:
        print ('Directory does not exist');
    os.makedirs(sourceFolder);

    for rule in rules:
        for f in originalFiles:
            shutil.copy(f, sourceFolder);
        sp.call(['java', '-cp', 'target/sonarqube-repair-0.1-SNAPSHOT-jar-with-dependencies.jar', 'Main', rule], cwd = SQR)

        # Go over all Spooned files and compare them to originals. If a diff is found, replace it.
        path = SQR + '/spooned'
        spoonedFiles = [];
        for r, d, f in os.walk(path):
            for file in f:
                if '.java' in file:
                    spoonedFiles.append(os.path.join(r, file))

        for o in originalFiles:
            for s in spoonedFiles:
                if(o.split('/')[-1] == s.split('/')[-1]):
                    if(not filecmp.cmp(o, s)):
                        shutil.copy(s, o);
                    break;

    # Save the project URL
    url = os.environ['TRAVIS_JOB_WEB_URL'];
    owner = url.split('/')[-4];
    project = url.split('/')[-3];
    # Make a commit to the branch and push it
    sp.call(['git', 'commit', '-a', '-m', 'Repairs Sonarqube violations']);
    # HTTPS will be used by default. This forces SSH usage.
    sp.call(['git', 'remote', 'set-url', 'origin', 'git@github.com:' + owner + '/' + project + '.git']);
    sp.call(['git', 'push', 'origin', branch]);
else:
    print("Wrong branch or PR");
