# Data crawling 

## Target
- Từ dữ liệu báo cáo cổ phiếu của 1 công ty (Sheet HNX, HOSE) từ nhiều nhà phân tích (Ngân hàng, CTCK), thu thập những thông tin về EPS (Earnings Per Share) dự báo, EPS thực, theo quý và năm

| name      | sec_code | stock_exchange | eps_actual | eps_forecast | analyst | report_date | stock_price_before | quarter | year |
|-----------|----------|---------------|------------|--------------|---------|-------------|--------------------|---------|------|
| Vinamilk  | VNM      | HOSE          | 3.5        | 3.2          | FPTS    | 2024-07-25  | 65.6               | Q2      | 2024 |

## Sources
Source type | Columns
|--|--|
|TradingView| quarterly eps_actual, quarterly eps_forecast, yearly eps_actual, yearly eps_forecast, analyst, report_date, stock_price_before|
|Brokerage (FPTS, VNDIRECT, SSI, VCBS, MBS, VCSC)| quarterly eps_actual, quarterly eps_forecast, yearly eps_actual, yearly eps_forecast, analyst, report_date, stock_price_before|
|HNX, HOSE| quarterly eps_actual |

## Strategy

### Libraries
- Sử dụng `pandas` để đọc dữ liệu từ các nguồn khác nhau.
- Sử dụng `requests` để lấy dữ liệu từ TradingView và các trang web của các công ty chứng khoán.
- Sử dụng `BeautifulSoup` để phân tích cú pháp HTML và trích xuất thông tin cần thiết.
- Lưu dữ liệu vào định dạng CSV hoặc cơ sở dữ liệu để dễ dàng truy xuất và phân tích sau này.
- Sử dụng `datetime` để xử lý ngày tháng và phân loại dữ liệu theo quý và năm.
- Vì 1 số nguồn dữ liệu từ pdf, nên cần sử dụng thêm thư viện `PyMuPDF` để trích xuất dữ liệu từ file PDF.

### Process
1. **Thu thập dữ liệu từ TradingView**:
   - Sử dụng API hoặc web scraping để lấy dữ liệu EPS thực và dự báo theo quý và năm.
   - Lưu trữ dữ liệu vào DataFrame với các cột: `name`, `sec_code`, `stock_exchange`, `eps_actual`, `eps_forecast`, `analyst`, `report_date`, `stock_price_before`, `quarter`, `year`.