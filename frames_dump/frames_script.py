# Paste this code into the function or test section 
# you want to find out which frame is which, in order to send to the chatGPT the hierrarchy of frames and their content,
# to be able to write the correct locators for the elements in the page. 


import os

os.makedirs("frames_dump", exist_ok=True)

for i, fr in enumerate(page.frames):
    try:
        name = fr.name or f"frame_{i}"
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
        with open(f"frames_dump/{i}_{safe_name}.html", "w", encoding="utf-8") as f:
            f.write(fr.content())
        print(f"Saved: {i}_{safe_name}.html | url={fr.url}")
    except Exception as e:
        print(f"Failed frame {i}: {e}")