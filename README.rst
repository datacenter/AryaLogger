==========
AryaLogger
==========

Use the SimpleAciUiLogServer and arya to convert UI REST API calls to ACI
Python SDK code.

Install
-------

Installation of AryaLogger depends on several other modules that are not part
of the Python standard library.  Here is a basic list of those modules:

1. acicobra - Not yet available on Pypi
2. arya - Not yet available on Pypi
3. SimpleAciUiLogServer - available on Pypi

Installing Dependancies
+++++++++++++++++++++++

The two difficult dependancies to install are aray and acicobra.

Installing acicobra
"""""""""""""""""""

If you have at least APIC version 1.0(3f) installed on your APIC, installation
of acicobra can be done by simply pointing pip at your APIC's cobra/_downloads
directory using the --find-links option using one of these two commands:

    pip install -Z --find-links http://apic/cobra/_downloads acicobra

Or:

    pip install -Z --find-links https://apic/cobra/_downloads acicobra

If your APIC has http disabled (the default), you must either use https or
enable http on the APIC.

If you have an older version of software on your APIC, you can either download
acicobra from the Cisco.com software download site (APIC specific contract
required to be tied to the Cisco.com id doing the download) or you can download
the acicobra egg from the APIC itself and rename it:

    https://developer.cisco.com/media/apicDcPythonAPI_v0.1/install.html

Installing arya
"""""""""""""""

Arya is currently (as of March 2015) contained in a subdirectory of the ACI
repo on github.  Installation of arya simply requires you to clone that
repository, change to the arya directory and run python against arya's setup.py
with the install option:

    cd some/directory/you/want/
    git clone https://github.com/datacenter/ACI.git
    cd ACI/arya
    python setup.py install

Installing AryaLogger
+++++++++++++++++++++

AryaLogger is available on pypi so installation is fairly straight forward:

    pip install AryaLogger

This should also pull in SimpleAciUiLogServer if you don't have it installed
already.

Run AryaLogger
--------------

There are two possible commands to run AryaLogger on your system.  You only need
to run one of these commands:

    aryalogger

Or:

    AryaLogger

There are additional options available that can be seen via the -h option:

    $ aryalogger -h
    usage: Archive APIC Rest API calls in the PythonSDK syntax [-h] [-a APICIP]
                                                               [-po PORT]
                                                               [-l LOCATION]
                                                               [-s SSLPORT]
                                                               [-c CERT]
                                                               [-e [{subscriptionRefresh,aaaRefresh,topInfo} [{subscriptionRefresh,aaaRefresh,topInfo} ...]]]
                                                               [-r] [-n]
                                                               [-i INDENT]
    
    optional arguments:
      -h, --help            show this help message and exit
      -a APICIP, --apicip APICIP
                            If you have a multihomed system, where the apic is on
                            a private network, the server will print the ip
                            address your local system has a route to 8.8.8.8. If
                            you want the server to print a more accurate ip
                            address for the server you can tell it the apicip
                            address.
      -po PORT, --port PORT
                            Local port to listen on, default=8987
      -l LOCATION, --location LOCATION
                            Location that transaction logs are being sent to,
                            default=/apiinspector
      -s SSLPORT, --sslport SSLPORT
                            Local port to listen on for ssl connections,
                            default=8443
      -c CERT, --cert CERT  The server certificate file for ssl connections,
                            default="server.pem"
      -e [{subscriptionRefresh,aaaRefresh,topInfo} [{subscriptionRefresh,aaaRefresh,topInfo} ...]], --exclude [{subscriptionRefresh,aaaRefresh,topInfo} [{subscriptionRefresh,aaaRefresh,topInfo} ...]]
                            Exclude certain types of common "noise" queries.
      -r, --logrequests     Log server requests and response codes to standard
                            error
      -n, --nice-output     Pretty print the response and payload
      -i INDENT, --indent INDENT
                            The number of spaces to indent when pretty printing

For HTTPS, AryaLogger does come with a default certificate file but it should
not be used for production.  Instead you should create your own certificate file
using openssl and pass it to the server:

    openssl req -new -x509 -keyout server.pem -out server.pem -days 36500 -nodes

Pass it in to AryaLogger using the -c/--cert option.

Setup your APIC
---------------

Setting up your APIC to send log messages to AryaLogger is very simple as well.
When you run AryaLogger it will output the addresses and ports it is listening
to:

    $ aryalogger
    serving at:
    http://10.1.1.100:8987/apiinspector
    https://10.1.1.100:8443/apiinspector

If you connect to the APIC graphical user interface (GUI) via http, take note of
the http URL otherwise if you connect to the GUI using https take note of
the https URL.

Use this URL in the 'Start Remote Logging' pop-up that is available from the 
'Welcome' menu at the top right of the GUI.

Once you have started remote logging to the URL provided by AryaLogger, when you
click around the APIC GUI you should see auto generated Cobra SDK code from
AryaLogger.

