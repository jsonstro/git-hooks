#! /opt/csw/bin/python
# Written by Josh Sonstroem (jsonstro@ucsc.edu) for the UCSC DCO.Unix team on 3,5 July 2013
" Subversion visudo pre-commit hook. "

def _mkdir(newdir):
    import os
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
        """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)
        # print "_mkdir %s" % repr(newdir)
        if tail:
            os.mkdir(newdir)

def command_output(cmd):
    " Capture a command's standard output. "
    import subprocess
    sys.stderr.write(cmd + "\n")
    return subprocess.Popen(
                            cmd.split(), stdout=subprocess.PIPE).communicate()[0]

def files_changed(look_cmd):
    """ List the files added or updated by this transaction.
        
        "svnlook changed" gives output like:
        U   trunk/file1.cf
        A   trunk/sudoers-group
        """
    def filename(line):
        return line[4:]
    def added_or_updated(line):
        # print line
        return line and line[0] in ("A", "U")
    return [
            filename(line)
            for line in command_output(look_cmd % "changed").split("\n")
            if added_or_updated(line)]

def file_contents(filename, look_cmd):
    " Return a file's contents for this transaction. "
    return command_output(
                          "%s %s" % (look_cmd % "cat", filename))

def chk_sudoers_file(fname):
    " Return the path to the sudoers file in the repo if matches filetype sudoers. "
    import os, re
    tpath = os.path.splitext(fname)[0]
    match = re.search('\w*sudoers\-\w*', tpath)
    if match:
        # print(tpath)
        return[tpath]
    # else:
        # print("No match")

def visudo_file(filename, look_cmd):
    " Return True if this version of the file is parsable by visudo -c. "
    import subprocess, os
    fn = chk_sudoers_file(filename)
    ### cat file contents to temp location to check
    temp_contents = file_contents(filename, look_cmd)
    directory = "/opt/app/svn/temp/"
    if not os.path.exists(directory):
        _mkdir(directory)
    filename_temp = directory + "sudoers.tmp"
    f = open(filename_temp, 'w')
    f.write(temp_contents)
    f.close()
    logfile = "/opt/app/svn/log/visudoers.log"
    l = open(logfile, 'a+')
    l.write(filename)
    l.write("\n")
    l.close()
    # print ("Checking %s (%s)") % (filename_temp,filename)
    v = subprocess.call(['/opt/csw/sbin/visudo', '-c', '-f', filename_temp])
    return bool(not v)

def validate_sudoers_files(look_cmd, txn_o_rvn):
    " Check that sudoers files in this transaction are parsable. "
    def is_sudoers_file(fname):
        import os, re
        tpath = os.path.splitext(fname)[0]
        match = re.search('\w*sudoers\-\w*', tpath)
        if match:
            # print(tpath)
            rname = 1
        else:
            # print("No match")
            rname = 0
        return rname
    import datetime, os
    now = datetime.datetime.now()
    directory = "/opt/app/svn/log/"
    if not os.path.exists(directory):
        _mkdir(directory)
    logfile = directory + "visudoers.log"
    l = open(logfile, 'a+')
    l.write(str(now) + ": ")
    l.write("TXN/RVN #" + txn_o_rvn + "\n")
    l.close()
    sudoers_files_that_are_invalid = [
                                      ff for ff in files_changed(look_cmd)
                                      if is_sudoers_file(ff) and not visudo_file(ff, look_cmd)]
    # print(sudoers_files_that_are_invalid)
    if len(sudoers_files_that_are_invalid) > 0:
        sys.stderr.write("The following sudo files contain errors and will not parse:\n%s\n"
                         % "\n".join(sudoers_files_that_are_invalid))
        l = open(logfile, 'a+')
        l.write("The following sudo files contain errors and will not parse:\n%s\n"
                % "\n".join(sudoers_files_that_are_invalid))
        l.write("\n")
        l.close()
    else:
        # print("Sudoers parsed successfully")
        sys.stderr.write("Sudoers parsed successfully\n")
    return len(sudoers_files_that_are_invalid)

def main():
    usage = """usage: %prog REPOS TXN
        
        Run pre-commit options on a repository transaction."""
    from optparse import OptionParser
    parser = OptionParser(usage=usage)
    parser.add_option("-r", "--revision",
                      help="Test mode. TXN actually refers to a revision.",
                      action="store_true", default=False)
    errors = 0
    try:
        (opts, (repos, txn_or_rvn)) = parser.parse_args()
        look_opt = ("--transaction", "--revision")[opts.revision]
        look_cmd = "/opt/csw/bin/svnlook %s %s %s %s" % (
                                                         "%s", repos, look_opt, txn_or_rvn)
        errors += validate_sudoers_files(look_cmd, txn_or_rvn)
    except:
        parser.print_help()
        errors += 1
    return errors

if __name__ == "__main__":
    import sys
    sys.exit(main())
