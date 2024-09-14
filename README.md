# ComSlator

ComSlator is a web application designed to provide real-time translation and other AI-powered features. The project is developed by a team of students as part of their coursework and aims to enhance language learning and communication.

## Contributors

- [UNO TOMOKI](https://github.com/AL23075)
- [KOTAKI NAOSHIGE]()
- [PHAM QUOC CUONG](https://github.com/cuonggpham)
- [TRAN CAO BAO PHUC](https://github.com/Phuctran11)
- [NGUYEN MANH QUAN](https://github.com/Kuan-niisan)

## Features

- Real-time translation between Japanese, Vietnamese, and English with a simple click.
- AI-powered functionalities integrated into the website.
- User-friendly interface.

## Technology

- Python 3.x
- Django
- Virtualenv

## Installation

Follow these steps to set up the project on your local machine:

1. **Clone the repository using the command below:**
   
        git clone https://github.com/AL23075/Comslator.git
2. **Move into the directory where the project files are located:**
    
        cd Comslator
3. **Create a virtual environment:**
   
        # Let's install virtualenv first
        pip install virtualenv

        # Then we create our virtual environment
        virtualenv envname
4. **Activate the virtual environment:**

        # On Windows
        envname\scripts\activate

        # On Unix or MacOS
        source envname/bin/activate
5. **Install the required packages:**
   
        pip install -r requirements.txt
7. **Running the App:**

To run the app, use the following command:

    python manage.py runserver

> Then, the development server will be started at http://127.0.0.1:8000/.