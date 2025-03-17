#!/usr/bin/env python

def is_env_notebook():
    """Determine wheather is the environment Jupyter Notebook"""
    if 'get_ipython' not in globals():
        # Python shell
        return False
    env_name = get_ipython().__class__.__name__
    if env_name == 'TerminalInteractiveShell':
        # IPython shell
        return False
    # Jupyter Notebook
    return True

#%%
from collections import deque
import matplotlib.pyplot as plt
import pyautogui
import numpy as np
from PIL import Image
import easyocr
import cv2
import requests
import re

#%%
reader = easyocr.Reader(['en'])
#%%
region = (700 , 1600, 1000, 400)
#pil_img = pyautogui.screenshot(region=(500 ,1500, 1000, 400))
#pil_img = pyautogui.screenshot(region=(300 ,700, 700, 300))
if is_env_notebook():
    pil_img = pyautogui.screenshot(region=region)
    img = np.asarray(pil_img)
    plt.imshow(img)
    result = reader.readtext(img, detail=0)
    print(result)

#%%
class SentenceBuffer:
    def __init__(self, size=10):
        self.q = deque([])
        self.size = size

    def add(self, sentences:list[str]) -> list[str]:
        new_sentences = []
        for s1 in sentences:
            found = False
            for s2 in self.q:
                if s1 == s2:
                    found = True
                    break
            if not found:
                new_sentences.append(s1)
        for new_s in new_sentences:
            if len(self.q) >= self.size:
                self.q.popleft()
            self.q.append(new_s)
        return new_sentences

sb = SentenceBuffer(size=10)

li = 0
while True:
    li += 1
    #pil_img = pyautogui.screenshot(region=(500 ,1500, 1000, 400))
    pil_img = pyautogui.screenshot(region=region)
    img = np.asarray(pil_img)
    ocr_parts = reader.readtext(img, detail=0)
    parts = []
    for part in ocr_parts:
        if "XXX" in part or "YYY" in part:
            continue
        parts.append(part)
    tmp_line = " ".join(parts)
    #print(tmp_line)
    sentences = re.split('[.;:,]', tmp_line)
    new_sentences = sb.add(sentences)
    print(f"OCR {li}")
    #for i, new_s in enumerate(new_sentences, 1):
    #    print(f"  {i} {new_s}")
    server = "http://localhost:8080"
    for i, text_in in enumerate(new_sentences, 1):
        res = requests.post(server, text_in)
        print(f"  {i} {text_in}")
        print(f"    {res.text}")

    if i >= 10:
        break
