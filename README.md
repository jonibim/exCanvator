# exCanvaTor 

> ⚠️ Project is still undergoing development

Scope of project is to download ALL possible files from Canvas.

It seems that courses in Canvas do not follow a standard, some do have a Files section, some do not expose it, and some
expose this section, but some files are not shown there. Instead, we have to navigate through the modules section. And again, some courses don't have a Module section at all, but instead have a Syllabus...and sometimes they don't have that as well, but only a homepage. For this reason, beside getting as much info as we can using the standard API calls, there is also a crawler, with a goal of getting as many canvas LINKS as possible to download and store. 

Currently the following will be downloaded:
- _Files_ (if they are accessible)
- _Assignments_ (with their description and score you got, currently the assignment itself if its in the body of the page, it is not guaranteed to be downloaded)
- _Modules_ (and all the files specified in the modules)
- _Pages_ (every possible page that is reachable from either homepage or syllabus is downloaded)

Files that cannot be downloaded are logged into `logs/ignored.txt`. More support for more files and edge cases should be added in the future. 

## Quick setup 

Create a virtual environment. Install the required packages for Python. Finally, configure with your Canvas domain that your university/school uses. 
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```



