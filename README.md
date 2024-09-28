# exCanvaTor 🚧

Scope of project is to download ALL files from Canvas.

However, courses in Canvas do not follow a standard, some do have a Files section, some do not expose it, and some
expose this section, but some files are not shown there. Instead, we have to navigate through the modules section. And again, some courses don't have a Module section at all, but instead have a Syllabus...and sometimes they don't have that as well, but only a homepage. For this reason, beside getting as much info as we can using the standard API calls, there is also a crawler, with a goal of getting as many canvas LINKS as possible to download and store. 



## Quick setup 

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```


- Fix Crawler not fully crawling properly
    - Handle edge cases of ids
    - Look into fetching assignments
    - Stop fetching what has been fetched before
- Shit ton of refactor
    - Restructure files completely
    - Remove duplication
    - DeChatGPT the code

