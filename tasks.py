import os
import shutil

from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF

pdf = PDF()

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    # browser.configure(
    #     slowmo=200,
    # )

    create_directories()
    open_robot_order_website()
    orders = get_orders()
    for order in orders:
        fill_the_form(order)

    archive_receipts()

def create_directories():
    os.makedirs("output/receipts-pdf", exist_ok=True)
    os.makedirs("output/robot-imgs", exist_ok=True)

def open_robot_order_website():
    browser.goto("https://robotsparebinindustries.com/#/robot-order")
    close_annoying_modal()

def get_orders():
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)

    tables = Tables()
    table = tables.read_table_from_csv("orders.csv")

    return table

def close_annoying_modal():
    page = browser.page()
    page.click("text=OK")

def fill_the_form(order):
    page = browser.page()
    page.select_option("#head", order["Head"])
    page.click(f"id=id-body-{order['Body']}")
    page.fill("//input[@placeholder='Enter the part number for the legs']", order["Legs"])
    page.fill("#address", order["Address"])

    while True:
        page.click("#order")
        
        if not page.locator("//div[@class='alert alert-danger']").is_visible():
            break

    pdf_file_path = store_receipt_as_pdf(order["Order number"])
    img_file_path = screenshot_robot(order["Order number"])

    embed_screenshot_to_receipt(img_file_path, pdf_file_path)

    page.click("#order-another")

    close_annoying_modal()

def store_receipt_as_pdf(order_number):
    page = browser.page()
    sales_results_html = page.locator("#receipt").inner_html()

    file_path = f"output/receipts-pdf/{order_number}.pdf"
    pdf.html_to_pdf(sales_results_html, file_path)

    return file_path

def screenshot_robot(order_number):
    page = browser.page()
    locator = page.locator("#robot-preview-image")
    img_bytes = browser.screenshot(element=locator)

    file_path = f"output/robot-imgs/{order_number}.png"
    with open(file_path, 'wb') as img_file:
        img_file.write(img_bytes)

    return file_path

def embed_screenshot_to_receipt(screenshot, pdf_file):
    pdf.add_files_to_pdf(
        files=[screenshot],
        target_document=pdf_file,
        append=True
    )

def archive_receipts():
    shutil.make_archive("output/receipts-pdf", 'zip', "output/receipts-pdf")
