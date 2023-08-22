#! .langchain_venv/bin/python

from bs4 import BeautifulSoup
import sys

with open(sys.argv[1], "r", encoding="utf-8") as file:
    content = file.read()

soup = BeautifulSoup(content, "lxml")

# Find the element using the CSS selector
# element = soup.select_one('body > div.elementor.elementor-1493.elementor-location-single.post-11129.post.type-post.status-publish.has-post-thumbnail.hentry.category-speakers-2023')
element = soup.select_one(
    "body > div.elementor.elementor-1493.elementor-location-single.post-10748.post.type-post.status-publish.has-post-thumbnail.hentry.category-all > section > div > div > div > section.elementor-section.elementor-inner-section.elementor-element.elementor-element-7f6e5736.elementor-section-boxed.elementor-section-height-default > div > div > div > div.elementor-element.elementor-element-e3cb0fa.elementor-widget.elementor-widget-theme-post-content > div > div"
)
#                          body > div.elementor.elementor-1493.elementor-location-single.post-9613.post.type-post.status-publish.has-post-thumbnail.hentry.category-all > section > div > div > div
if element:
    # Extract the text from the element and its children
    extracted_text = element.get_text(separator="\n", strip=True)
    print(extracted_text)
else:
    pass
    # print("Element not found!")

title_time_element = soup.select_one(
    "body > div.elementor.elementor-1493.elementor-location-single.post-9073.post.type-post.status-publish.has-post-thumbnail.hentry.category-all > section > div > div > div > section.elementor-section.elementor-inner-section.elementor-element.elementor-element-6dbbdcb.elementor-section-boxed.elementor-section-height-default > div > div.elementor-column.elementor-col-50.elementor-inner-column.elementor-element.elementor-element-b538cd9 > div"
)
if title_time_element:
    extracted_text = title_time_element.get_text(separator="\n", strip=True)
    print(extracted_text)


spans = soup.find_all("span", attrs={"data-sheets-value": True})

enclosed_texts = [span.text for span in spans]
enclosed_text = "\n".join(enclosed_texts)
print(enclosed_text)
