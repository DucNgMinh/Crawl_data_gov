import cv2
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import pytesseract
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service 
import re
import time

ds_xa = [ 8051905, 8051911, 8051907, 8051923]

index = 0

def get_captcha(driver):
    # Lấy bản chụp màn hình dưới dạng dữ liệu PNG
    screenshot = driver.get_screenshot_as_png()

    # Chuyển đổi dữ liệu PNG thành mảng NumPy
    screenshot_array = np.frombuffer(screenshot, np.uint8)

    # Đọc hình ảnh từ mảng NumPy
    image = cv2.imdecode(screenshot_array, cv2.IMREAD_COLOR)

    # Cắt ảnh
    x1, y1, x2, y2 = (700, 563, 837, 613)
    crop = image[y1:y2, x1:x2]
    cv2.imwrite("crop.png", crop)

    resized_image = cv2.resize(crop, (390, 150))
    blurred_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)

    kernel = np.ones((6,6), np.uint8)
    dilation = cv2.dilate(blurred_image, kernel, iterations=1)

    for row in range(len(dilation)):
        for col in range(len(dilation[row])):
            if dilation[row, col] < 150:
                dilation[row, col] = 0
            else:
                dilation[row, col] = 255

    dilation = cv2.medianBlur(dilation, 5, 0)

    height, width = dilation.shape

    # Kích thước mới (tăng thêm 30 pixel ở dưới)
    new_height = height + 30
    new_width = width

    # Tạo một hình ảnh mới với kích thước mới và màu trắng
    new_image = np.zeros((new_height, new_width), dtype=np.uint8)
    new_image[:] = (255)  # Gán màu trắng (255, 255, 255)

    # Sao chép hình ảnh gốc vào hình ảnh mới
    new_image[:height, :] = dilation

    # Trích xuất văn bản từ hình ảnh
    text = pytesseract.image_to_string(new_image,nice = 20,config='--psm 13')

    #xóa các kí tự punctuation
    text = re.sub(r'[^\w\s]', '', text)

    # Loại bỏ các khoảng trắng thừa
    text = ''.join(text.split())

    return text

def test_captcha(driver,captcha):
    if len(captcha) != 5:
        return False
        
    url = f"https://www.gdt.gov.vn/TTHKApp/jsp/results.jsp?maTinh=805&maHuyen=80511&maXa=&hoTen=&kyLb=&diaChi=&maSoThue=&searchType=11&uuid=d01567b7-cb8b-47ae-b3b7-dfd6132076c4&captcha={captcha}&pageNumber=1"
    driver.get(url)
    element = driver.find_element(By.XPATH, '/html/body/div[1]')
    if element.text == "Vui lòng nhập đúng mã xác nhận.":
        return False
    driver.save_screenshot("screenshot.png")
    return True

def refresh_captcha(driver):
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, '#nntSearchForm > div:nth-child(9) > div > img').click()
    
def main():
    global index
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    path = r'C:\Users\Admin\Documents\OneNoteNotebooks\20222\BigData\chromedriver.exe'
    service = Service(path)
    driver = webdriver.Chrome(service=service)

    # Truy cập trang web
    

    while True:
        driver.get("https://www.gdt.gov.vn/wps/portal/home/hct")
        time.sleep(1)
        captcha = get_captcha(driver)

        if test_captcha(driver,captcha):
            print(f"captcha is correct:{captcha}")
            # print(len(captcha))
            break
        # refresh_captcha(driver)
    

    # ds_xa = [1015149, 1015135, 1015139, 1015131, 1015121, 1015107, 1015123]
    for i in range(len(ds_xa)):
        xa = ds_xa[i]
        index = i
        xa = str(xa)
        tinh = str(xa[:3])
        huyen = str(xa[:5])
        search_types = {'11':'/html/body/div[4]/table',
                        '10':'/html/body/table',
                        '12':'/html/body/div[4]/table',
                        '03':'/html/body/div[4]/table',
                        '04':'/html/body/table'}
        
        for type in search_types:
            df = pd.DataFrame()
            for page in range(1,100):
                url = f"https://www.gdt.gov.vn/TTHKApp/jsp/results.jsp?maTinh={tinh}&maHuyen={huyen}&maXa={xa}&kyLb=&searchType={type}&captcha={captcha}&pageNumber={page}"
                driver.get(url)

                notify_element = driver.find_element(By.XPATH, '/html/body/div[1]')
                if notify_element.text == "Không tìm thấy kết quả":
                    break

                table_element = driver.find_element(By.XPATH,search_types[type])
                tables = pd.read_html(table_element.get_attribute("outerHTML"))
                if len(tables[0]) < 5:
                    break
                tables[0]['mã_tỉnh'] = tinh
                tables[0]['mã_huyện'] = huyen
                tables[0]['mã_xã'] = xa
                tables[0]['search_type'] = type
                df=pd.concat([df,tables[0]])
        # driver.save_screenshot(f"screenshot_{tinh}_{huyen}_{page}.png")
            path1 = f'C:\\Users\\Admin\\Documents\\BIDV\\data\\{tinh}_{huyen}_{xa}_{type}.csv'
            df.to_csv(path1,index=False,encoding='utf-8-sig')
            print(f"Done {tinh}_{huyen}_{xa}_{type}.csv")
    driver.quit()
    # return df

if __name__ == "__main__":
    while True:
        try:
            main()
            if index == len(ds_xa)-1:
                break           
        except:
            print(f"Error at {ds_xa[index]}")
            ds_xa = ds_xa[index:]

    
