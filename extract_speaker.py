#! .langchain_venv/bin/python
from bs4 import BeautifulSoup
import sys

with open(sys.argv[1], "r", encoding="utf-8") as file:
    html_content = file.read()
#
# soup = BeautifulSoup(content, 'lxml')
#
# # Find the element using the CSS selector
# element = soup.select_one('body > div.elementor.elementor-1493.elementor-location-single.post-11129.post.type-post.status-publish.has-post-thumbnail.hentry.category-speakers-2023')
#
# if element:
#     # Extract the text from the element and its children
#     extracted_text = element.get_text(separator='\n', strip=True)
#     print(extracted_text)
# else:
#     print("Element not found!")
soup = BeautifulSoup(html_content, "html.parser")

spans = soup.find_all("span", attrs={"data-sheets-value": True})

enclosed_texts = [span.text for span in spans]
enclosed_text = "\n".join(enclosed_texts)
print(enclosed_text)
