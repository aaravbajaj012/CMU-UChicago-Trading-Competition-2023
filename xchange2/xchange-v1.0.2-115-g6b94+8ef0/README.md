# UTC 2023 - Setup Instructions & Case Details

Hello everyone! We're the UChicago Trading Competition casewriting and platform development team.
This document contains all of the information you need to set up your environment and start
developing bots for cases 1 and 2. **We recommend that you read this entire document from start to
finish and follow the instructions carefully. If you have any questions about anything in this
document, please do not hesitate to contact us via Piazza**.

## Supported Software
We will be providing technical support only for competitors who write their bots in the Python
programming language and use Visual Studio Code as their editor. Instructions on how to install
these two pieces of software are below. It is possible to use other programming languages, but
significantly more difficult.

We also expect a very basic level of familiarity with the command prompt (if you have a Windows
computer) or terminal (if you have a Mac). If you are not yet familiar with these tools, there are a
number of very helpful tutorials available online.

### Python 3.9+ Installation
We ask that you install Python version 3.9 or later. To get the download links for your operating
system, visit <https://www.python.org/downloads/>.

After installing Python, you should open a new command prompt/terminal and type

	python3 --version

**NOTE**: on Windows, you may need to replace `python3` with `py`.

> - **If you see an error message instead**, it is likely that you need to add Python to your PATH
>   environment variable. There are a number of resources online that detail how to do this. If the
>   error persists, contact the platform developers.
> - **If the version number you see is less than 3.9.0**, you will need to upgrade your Python
>   installation. In this case, download the latest version of Python from the link above, and the
>   installer should automatically upgrade your version of Python.

### Visual Studio Code Installation
To download VS Code, please visit <https://code.visualstudio.com/>.

After downloading the editor, open the folder containing this file. The editor should automatically
suggest that the Python and Pylance extensions be installed. We strongly recommend that you install
these--they will offer a much easier development experience once you get started working on your
bots.

## Platform Setup
The platform for the trading competition consists of two main parts:
- The *clients*, which are the bots that you will write that will trade against each other and the
  market
- The *exchange*, which the clients will connect to send order request/receive data feeds about the market

Some notes on how to set up and use these parts follow.
### Client Setup & Usage
When you first download a new version of the platform, you will need to set it up before using it.
To do this, navigate to the directory containing the platform (using the `cd` command) and run

    python3 setup-xchange.py

**NOTE**: on Windows, you may need to replace `python3` with `py`.

If all goes well, a message saying **<span style="color:green">Everything is set up!</span>** should
appear.
> **If you see red text that says <span style="color:red">Error: ...</span>**, then read the error message and follow the corresponding instructions. If errors persist, please contact the platform team via Piazza.

After running the above command successfully, a new *virtual environment* will have been set up in
the directory. For more details on what a virtual environment is and how to use them, please visit
<https://docs.python.org/3/tutorial/venv.html>.

To activate this virtual environment, type:

 - `.\venv\Scripts\activate` (if you're on Windows)
 - `source venv/bin/activate` (if you're on Mac/Linux)

If this is successful, there should be a `(venv)` before your command line, which indicates that the
environment is currently active. **You should make sure to always run your bots with the environment
active**.

This virtual environment comes pre-installed with some useful packages:
 - `numpy` - A very popular scientific computing package
 - `pandas` - A very popular data analysis package
 - `scipy` - A popular scientific computing package with extended functionality
 - `py_vollib` - A package for computing option prices, greeks, and implied volatilities
 - `betterproto` - An interface with protocol buffers, which the bot uses under the hood to
   communicate with the platform

While in the virtual environment, you can run a bot by running

    python bot_name.py

### Exchange Details
This folder contains 3 copies of the exchange, one for each major operating system. **For the
remainder of the document, we will use `<xchange>` to refer to**:

 - `.\xchange-win.exe` if you're on Windows
 - `./xchange-mac` if you're on Mac
 - `./xchange-linux` if you're on Linux

For details on how each of these applications work, run

    <xchange> -help

Details about how to use the platform for the cases will follow.

## Getting Started!
**In order to test your bots before the competition, you will need to run both your bot and the
exchange _at the same time_ on your computer**. This means that you will have to open two different
command line windows, one in which the virtual environment is activated (in which you can run your
bot), and one where you will run the exchange. While the exchange is running, you can visit
<http://localhost:8080> in your browser for a real-time display of what is occurring in the markets.

Details on how to run the exchange for each case are in the following sections
### Case 1
#### Instructions
Before the exchange has started, begin the execution of your bot in a separate command line window.
To test that everything is working, you can start by running the example bot by typing

    python clients/example_bot_case1_2023.py

After your bot has been started, it will wait to connect to the exchange. To run the exchange for
Case 1, open a separate command line window and execute

    <xchange> 2023_case1.yaml

so that both your bot and the exchange are running at the same time. Soon after this, your bot
should print a message saying that it connected to the exchange, and it will start running.

We strongly recommend that you start your bot development by taking a close look at the example bot
and understanding how it works. It provides a good example of how to interact with the exchange for
this case.

### Case 2
#### Instructions
Before the exchange has started, begin the execution of your bot in a separate command line window.
To test that everything is working, you can start by running the example bot by typing

    python clients/example_bot_case2_2023.py

After your bot has been started, it will wait to connect to the exchange. To run the exchange for
Case 2, open a separate command line window and execute

    <xchange> 2023_case2

so that both your bot and the exchange are running at the same time. Soon after this, your bot
should print a message saying that it connected to the exchange, and it will start running.

We strongly recommend that you start your bot development by taking a close look at the example bot and understanding how it works. It provides a good example of how to interact with the exchange for this case, as well a strategy you may want to employ for adjusting your bot's parameters on the fly.

#### Data
The price paths used by case 2 can be found in the `data/case2/` folder.

## Questions
If you encounter any issues at all with the platform or cases while working on the competition,
please do not hesitate to contact the casewriters and/or platform team via Piazza.

If the question or problem is technical in nature, please run the `<xchange>` executable with the
`-debug` flag. Once the problem has been reproduced, use `Ctrl+C` to terminate the program, zip the
`xchange-logs` folder, and attach it to your Piazza post. This will allow the team to walk through
what is going on with the exchange and diagnose any problems that may be occurring.