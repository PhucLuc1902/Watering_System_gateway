# Tài Liệu Tổng Hợp – Công Nghệ Phần Mềm

> Tài liệu này tổng hợp toàn bộ nội dung lý thuyết và thực hành của môn **Công Nghệ Phần Mềm**, bao gồm các loại sơ đồ UML, yêu cầu hệ thống và kiểm thử phần mềm.

---

## Mục Lục

1. [Phần 1 – Yêu Cầu Hệ Thống](#phần-1--yêu-cầu-hệ-thống)
   - [1.1 Non-functional Requirements](#11-non-functional-requirements)
   - [1.2 Non-interactive Functional Requirements](#12-non-interactive-functional-requirements)
2. [Phần 2 – Use Case](#phần-2--use-case)
   - [2.1 Use Case Diagrams](#21-use-case-diagrams)
   - [2.2 Use Case Scenario](#22-use-case-scenario)
3. [Phần 3 – Sơ Đồ Hành Vi (Behavioral Diagrams)](#phần-3--sơ-đồ-hành-vi-behavioral-diagrams)
   - [3.1 Activity Diagrams](#31-activity-diagrams)
   - [3.2 Sequence Diagrams](#32-sequence-diagrams)
   - [3.3 State Machine Diagram](#33-state-machine-diagram)
4. [Phần 4 – Sơ Đồ Cấu Trúc (Structural Diagrams)](#phần-4--sơ-đồ-cấu-trúc-structural-diagrams)
   - [4.1 Class Diagram và Method Descriptions](#41-class-diagram-và-method-descriptions)
   - [4.2 Component Diagrams](#42-component-diagrams)
   - [4.3 Deployment Diagrams](#43-deployment-diagrams)
5. [Phần 5 – Kiểm Thử](#phần-5--kiểm-thử)
   - [5.1 Use-case Testing](#51-use-case-testing)

---

# Phần 1 – Yêu Cầu Hệ Thống

---

## 1.1 Non-functional Requirements

**Non-functional requirements là:**

Các yêu cầu mô tả **chất lượng và cách hệ thống hoạt động**,
không phải hệ thống làm *gì*, mà là làm **như thế nào**.

Khác với functional requirement (mô tả chức năng),
non-functional tập trung vào:

* Hiệu năng
* Bảo mật
* Độ tin cậy
* Khả năng mở rộng
* Khả năng bảo trì
* Tính sẵn sàng

**So sánh**

| Loại           | Trả lời câu hỏi                 | Ví dụ                   |
| -------------- | ------------------------------- | ----------------------- |
| Functional     | Hệ thống làm gì?                | Tính phí gửi xe         |
| Non-functional | Hệ thống hoạt động như thế nào? | Tính phí trong < 2 giây |

---

### 📌 Ví dụ đơn giản

#### 1️⃣ Performance (Hiệu năng)

> The system shall respond to parking entry requests within 2 seconds.

👉 Không chỉ "cho xe vào" mà phải nhanh.

---

#### 2️⃣ Availability (Tính sẵn sàng)

> The system shall maintain at least 99% uptime during operating hours.

👉 Hệ thống không được sập thường xuyên.

---

#### 3️⃣ Reliability (Độ tin cậy)

> The system shall continue operating even if one sensor fails.

👉 Một sensor hỏng không làm cả hệ thống ngừng.

---

#### 4️⃣ Security (Bảo mật)

> The system shall enforce role-based access control for all administrative functions.

👉 Chỉ admin mới được đổi giá.

---

#### 5️⃣ Scalability (Khả năng mở rộng)

> The system shall support at least 5,000 concurrent users.

👉 Phù hợp môi trường đại học đông người.

---

#### 6️⃣ Data Integrity (Toàn vẹn dữ liệu)

> The system shall ensure that all parking transactions are logged and cannot be modified without authorization.

👉 Không được sửa log tùy ý.

---

## 1.2 Non-interactive Functional Requirements

**Non-interactive functional requirements là:**

Các chức năng hệ thống thực hiện tự động,
không cần người dùng trực tiếp thao tác hoặc khởi tạo.

Khác với use-case kiểu:
- "User đăng nhập"
- "Admin cấu hình giá"
- "User thanh toán"

→ đó là interactive (có actor kích hoạt).

**So sánh**

| Loại               | Có Actor kích hoạt? | Ví dụ                        |
| ------------------ | ------------------- | ---------------------------- |
| Interactive FR     | Có                  | User quẹt thẻ                |
| Non-interactive FR | Không               | Hệ thống tự tính phí cuối kỳ |

---

### 📌 Ví dụ đơn giản

#### 1️⃣ Tự động tính phí cuối kỳ

> The system shall automatically calculate parking fees for students at the end of each billing period.

👉 Không ai bấm tính → hệ thống tự chạy theo lịch.

---

#### 2️⃣ Tự động cập nhật chỗ trống

> The system shall automatically update parking slot status when receiving sensor data.

👉 Sensor gửi dữ liệu → hệ thống tự xử lý.

---

#### 3️⃣ Tự phát hiện sensor lỗi

> The system shall automatically detect a sensor malfunction if no signal is received within 5 minutes.

👉 Không cần nhân viên kiểm tra thủ công.

---

#### 4️⃣ Tự gửi yêu cầu thanh toán

> The system shall automatically send payment requests to BKPay after fee calculation.

👉 Sau khi tính phí xong → hệ thống tự gửi.

---

# Phần 2 – Use Case

---

## 2.1 Use Case Diagrams

# Thành phần chính của Use Case Diagram

## Actor (tác nhân):

- **Actor** Một thực thể bên ngoài tương tác với hệ thống. Actor có thể là **một người (ví dụ: người dùng, quản trị viên, khách hàng)** hoặc một **hệ thống khác (ví dụ: hệ thống thanh toán, cơ sở dữ liệu bên ngoài)**.

- **Biểu diễn:** Hình que người (stick figure), thường có tên ở bên dưới.

- **Vai trò:** Đại diện cho một vai trò chứ không phải một người cụ thể. Một người thật có thể đóng nhiều vai trò (actor) khác nhau.

- **Ví dụ:** `Khách hàng`, `Quản trị viên`, `Kế toán`, `Giáo viên`, `Sinh viên`, `Hệ thống Email`. `Cổng thanh toán trực tuyến (PayPal, VNPay)`, `API của bên thứ ba`

![](https://www.uml-diagrams.org/use-case-diagrams/use-case-actor-rel-gener.png)

### Phân loại theo mức độ tương tác (Quan trọng trong phân tích)

- **Actor chính (Primary Actor):** Là actor khởi tạo Use Case để đạt được mục tiêu nào đó. Họ là người sử dụng hệ thống để nhận về giá trị trực tiếp.

**Ví dụ:** Trong Use Case "Đặt mua hàng", Khách hàng là Primary Actor vì họ là người chủ động thực hiện việc đặt hàng.

- **Actor phụ (Supporting Actor hoặc Secondary Actor):**  Là actor cung cấp dịch vụ cho hệ thống. Hệ thống cần tương tác với họ để hoàn thành Use Case. 

**Ví dụ:** Trong Use Case "Đặt mua hàng", hệ thống cần gọi tới Hệ thống thanh toán để xử lý giao dịch và gửi email xác nhận cho Khách hàng thông qua Hệ thống Email. Cả Hệ thống thanh toán và Hệ thống Email đều là Supporting Actors.

---

## Use Case (ca sử dụng):

- **Use Case** là một chức năng hoặc dịch vụ mà hệ thống **cung cấp cho actor** để đạt được một **mục tiêu cụ thể**. Nó mô tả "hệ thống làm gì" chứ không mô tả "làm như thế nào".

- **Biểu diễn:** Hình elip (oval) với tên use case bên trong.

- **Vai trò:** Mỗi use case thể hiện một tình huống sử dụng hệ thống có ý nghĩa đối với actor. Nó giúp trả lời câu hỏi: Actor có thể làm gì với hệ thống?

- **Ví dụ:** Đăng nhập, Đăng ký tài khoản, Thanh toán, Xem điểm.

![](https://miro.medium.com/v2/resize:fit:1400/1*Iiw_wByLHaYfFeb_oog3Dw.png)


### B1 - Đối Với Từng Actor, Đặt Câu Hỏi: "Actor Muốn Đạt Được Điều Gì?"
- Đây là **trọng tâm** của việc xác định Use Case. Mỗi Use Case phải cung cấp một giá trị có thể quan sát được cho một Actor.

- **Ví dụ** với Actor Khách hàng:
    - Họ muốn `"Duyệt danh mục sản phẩm"` -> Use Case `Duyệt sản phẩm`.
    - Họ muốn `"Mua một món hàng"` -> Use Case `Đặt mua hàng`.
    - Họ muốn `"Xem tình trạng đơn hàng của mình"` -> Use Case `Theo dõi đơn hàng`.
    - Họ muốn `"Được hỗ trợ khi có vấn đề"` -> Use Case `Liên hệ hỗ trợ`.

- Xác Định Các Use Case Liên Quan Đến Sự Kiện Theo Thời Gian hoặc Sự Kiện Hệ Thống Ví dụ:
    - `"Vào lúc 23h59 mỗi ngày, hệ thống cần thông báo"` -> Hệ thống sẽ gửi mail thông báo về lịch đã hẹn của sinh viên và giáo viên.

    - `"Khi đơn hàng không được thanh toán sau 24h, hệ thống cần hủy đơn"` -> Use Case Tự động hủy đơn hàng quá hạn.

### B2 - Nhóm Các Use Case Lại và Sử Dụng Các Quan Hệ `<<include>>` và `<<extend>>`

- Khi đã có một danh sách dài các Use Case, hãy xem xét những Use Case nào có chức năng chung.

- Ví dụ: Cả Đặt mua hàng và Cập nhật giỏ hàng đều cần Tính tổng tiền. Thay vì viết lại chức năng này, hãy tách nó thành một Use Case riêng Tính toán đơn giá và sử dụng quan hệ `<<include>>` để biểu thị rằng nó được bao gồm bắt buộc.

- Tương tự, tìm các chức năng tùy chọn (như Áp dụng mã giảm giá trong quá trình thanh toán) và sử dụng `<<extend>>`.

---

## Hệ thống (System boundary): 

- **Hệ thống (System boundary)** Nó định nghĩa phạm vi của phần mềm hoặc hệ thống bạn đang phân tích và thiết kế.

- **Mục đích:** Nó trả lời câu hỏi "Ranh giới giữa phần `bên trong` và `bên ngoài` hệ thống ở đâu?".
    - **Bên TRONG đường biên:** Là tất cả các chức năng (Use Case) mà hệ thống của bạn sẽ thực hiện.

    - **Bên NGOÀI đường biên:** Là tất cả các Actor (tác nhân) và các hệ thống bên ngoài mà hệ thống của bạn tương tác với.

- **Xác định phạm vi dự án:** Nó giúp ngăn "phạm vi bùng nổ" (scope creep) bằng cách làm rõ những gì thuộc về và không thuộc về hệ thống cần xây dựng.

- **Tập trung vào hệ thống hiện tại:** Nó buộc người phân tích phải tập trung vào các chức năng cốt lõi của hệ thống đang được đề cập, thay vì các hệ thống bên ngoài.

![](https://blog.visual-paradigm.com/wp-content/uploads/2022/10/use-case-diagram-multiple-projects-with-system-boundaries.png)

--- 

## Quan hệ (Relationships):

### Association (liên kết): Actor <-> Use case.

- **Association** là một đường thẳng (có thể có mũi tên hoặc không) kết nối trực tiếp một Actor với một Use Case.
- **Ý nghĩa:** Nó cho biết rằng Actor đó tham gia hoặc tương tác với Use Case đó. Actor có thể kích hoạt Use Case, cung cấp thông tin đầu vào cho nó, hoặc nhận thông tin đầu ra từ nó.
- **Ký hiệu:** Một đường thẳng liền nét.
- **Nguyên tắc kết nối:**
    - Một Actor có thể kết nối đến nhiều Use Case.
    - Một Use Case có thể được kết nối đến nhiều Actor.
    - Không bao giờ có kết nối trực tiếp giữa Actor với Actor hoặc Use Case với Use Case. Các kết nối này phải được thực hiện thông qua các quan hệ khác như `<<include>>` hoặc `<<extend>>`.

![](https://images.upgrad.com/7f187cfd-4b7c-4e8f-b4b7-08283d904876-zzz001.png)

### Include: Một use case luôn bao gồm use case khác.

- **`<<include>>`** thể hiện một mối quan hệ bắt buộc từ một Use Case này (gọi là Use Case cơ bản - base use case) đến một Use Case khác (gọi là Use Case được include - inclusion use case).
- **Ý nghĩa:** Hành vi của Use Case được include **LUÔN LUÔN được** thực thi như một phần không thể thiếu trong luồng sự kiện của Use Case cơ bản. Nó giống như việc gọi một hàm con hoặc một module có thể tái sử dụng.
- **Ký hiệu:** Một đường chấm chấm có mũi tên hướng từ **Use Case cơ bản ĐẾN Use Case được include**.
- **Khi nào sử dụng `<<include>>`**

    - **Tránh trùng lặp logic (Tính tái sử dụng):** Khi một đoạn hành vi (một nhóm các bước) giống nhau xuất hiện trong nhiều Use Case khác nhau.
    - **Ví dụ:** Cả Đặt mua hàng và Xem lịch sử đơn hàng đều bắt buộc phải Xác thực người dùng. Thay vì viết lại các bước xác thực trong cả hai Use Case, ta tách nó thành một Use Case riêng và dùng `<<include>>`.

        ![](https://www.uml-diagrams.org/use-case-diagrams/include-two-use-cases.png)


    - **Phân tách một Use Case phức tạp:** Khi một Use Case quá dài và có thể được chia nhỏ thành các phần độc lập về mặt logic. Phần được tách ra trở thành một Use Case được include.
    - **Ví dụ:** Use Case Đặt mua hàng rất phức tạp. Bạn có thể tách phần Tính toán phí vận chuyển thành một Use Case riêng và để Đặt mua hàng include nó.
        ![](https://www.uml-diagrams.org/use-case-diagrams/two-includes-use-case.png)
        ![](https://www.uml-diagrams.org/use-case-diagrams/include-use-case.png)

### Extend: Một use case có thể được mở rộng trong điều kiện cụ thể.

- **`<<extend>>`** thể hiện một mối quan hệ tùy chọn từ một Use Case này (Use Case mở rộng - extension use case) đến một Use Case khác (Use Case cơ bản - base use case).
- **Ý nghĩa:** Hành vi của Use Case mở rộng **chỉ được thực thi khi một điều kiện cụ thể xảy ra** trong quá trình thực thi Use Case cơ bản. Nó không phải là phần bắt buộc của luồng chính.
- **Ký hiệu:**  Một đường chấm chấm có mũi tên hướng từ **Use Case mở rộng ĐẾN Use Case cơ bản**.

![](https://www.jot.fm/issues/issue_2005_11/article4/images/figure3.gif)

### Generalization: Quan hệ kế thừa giữa actor hoặc use case.

- **Generalization** cho thấy rằng một thành phần cụ thể (con) kế thừa các đặc điểm và hành vi từ **một thành phần tổng quát hơn (cha)**, và **có thể mở rộng hoặc ghi đè chúng**.
- **Ý nghĩa:** Thành phần con `"là một"` dạng cụ thể của thành phần cha. Mọi kết nối (association, include, extend) của thành phần cha đều được áp dụng tự động cho thành phần con.
- **Ký hiệu:**  Một đường liền nét có mũi tên rỗng hình tam giác ở đầu, hướng từ thành phần con về phía thành phần cha.
- **Ví dụ:** Một Người dùng có thể thực hiện các Use Case chung như Đăng nhập và Xem trang cá nhân. Quản trị viên là một Người dùng, nên họ cũng có thể thực hiện những việc đó, đồng thời có thêm các quyền riêng như Quản lý người dùng.

![](https://www.uml-diagrams.org/use-case-diagrams/use-case-actor-rel-gener.png)

![](https://www.uml-diagrams.org/use-case-diagrams/use-case-generalization.png)

---

## 2.2 Use Case Scenario

# Thành phần chính của Use Case Scenario

## Một tài liệu Use Case chi tiết thường bao gồm các mục sau:

| Thành Phần       | Mô Tả                                                                                      | Ví Dụ (Cho Use Case "Rút Tiền" tại ATM)                                                                                                                                   |
|------------------|---------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1. Use Case Name** | Tên của Use Case.                                                                           | Rút Tiền                                                                                                                                                                 |
| **2. Use Case ID**   | Mã định danh duy nhất cho Use Case.                                                          | UC-101                                                                                                                                                                   |
| **3. Actor**         | Actor chính và actor phụ liên quan.                                                          | **Primary:** Khách hàng  <br> **Supporting:** Hệ thống Ngân hàng                                                                                                  |
| **4. Mô tả ngắn gọn**| 1-2 câu mô tả mục đích của Use Case.                                                         | "Cho phép khách hàng rút một số tiền mặt từ tài khoản ngân hàng của họ thông qua máy ATM."                                                                               |
| **5. Preconditions (Điều kiện tiên quyết)** | Các điều kiện bắt buộc phải đúng để Use Case có thể bắt đầu.                               | 1. Khách hàng đã có thẻ ATM.<br> 2. Máy ATM đang hoạt động và có tiền.<br> 3. Khách hàng đã đăng nhập thành công.                                                       |
| **6. Postconditions (Hậu điều kiện)** | Trạng thái của hệ thống sau khi Use Case kết thúc (dù thành công hay thất bại). | **Thành công:** <br>- Số tiền được trừ khỏi tài khoản.<br>- Giao dịch được ghi vào nhật ký.<br> **Thất bại:** <br>- Giao dịch được ghi vào nhật ký với trạng thái "lỗi". |
| **7. Basic Flow (Luồng chính - Happy Path)** | Luồng các bước khi mọi thứ diễn ra suôn sẻ và thành công. Đây là kịch bản mong đợi nhất. | 1. Khách hàng chọn chức năng "Rút tiền".<br> 2. Hệ thống yêu cầu nhập số tiền.<br> 3. Khách hàng nhập số tiền.<br> 4. Hệ thống kiểm tra số dư và tính khả dụng.<br> 5. Hệ thống đưa ra tiền và thẻ.<br> 6. Hệ thống in hóa đơn.<br> 7. Use Case kết thúc. |
| **8. Alternative Flows (Luồng thay thế)** | Các nhánh thay thế hoặc bổ sung cho luồng chính. Thường bắt đầu bằng "Tại bước X của luồng chính...". | **AF1: Số dư không đủ (Tại bước 4):** <br> 4.1. Hệ thống hiển thị thông báo "Số dư không đủ".<br> 4.2. Quay lại bước 2.<br><br> **AF2: Hủy giao dịch (Tại bước 2 hoặc 3):** <br> 2.1. Khách hàng nhấn nút "Hủy".<br> 2.2. Hệ thống trả lại thẻ và kết thúc. |
| **9. Exception Flows (Luồng ngoại lệ)** | Các tình huống lỗi hoặc sự cố bất ngờ. | **EF1: Máy ATM hết tiền (Tại bước 5):** <br> 5.1. Hệ thống hiển thị lỗi "Máy tạm thời hết tiền".<br> 5.2. Hệ thống hủy giao dịch và trả lại thẻ.<br><br> **EF2: Không kết nối được với ngân hàng:** <br> 4.1. Hệ thống hiển thị lỗi "Mất kết nối".<br> 4.2. Hủy giao dịch. |

---

## So sánh Alternative Flows và Exception Flows

| Đặc Điểm   | Alternative Flows (Luồng Thay Thế)                                      | Exception Flows (Luồng Ngoại Lệ)                             |
|------------|-------------------------------------------------------------------------|--------------------------------------------------------------|
| **Bản chất**   | Là các kịch bản hợp lệ, có thể dự đoán được.                           | Là các tình huống lỗi, sự cố bất thường.                     |
| **Nguyên nhân**| Do lựa chọn của Actor hoặc một điều kiện nghiệp vụ cụ thể.             | Do hệ thống lỗi, dữ liệu không hợp lệ, hoặc điều kiện ngoài dự kiến. |
| **Mục tiêu**   | Hoàn thành mục tiêu của Use Case theo một cách khác.                  | Xử lý lỗi một cách an toàn và thông báo cho Actor.            |
| **Kết quả**    | Vẫn có thể thành công và đạt được mục tiêu.                           | Thất bại trong việc đạt được mục tiêu chính.                  |
| **Tần suất**   | Có thể xảy ra thường xuyên.                                           | Hy vọng là ít khi xảy ra.                                     |
| **Ví dụ**      | Khách hàng chọn không in hóa đơn.                                     | Máy ATM hết tiền, mất kết nối mạng.                           |

---

## Độ tương quan của Use Case Diagram và use case Scenario

| Đặc Điểm            | Use Case Diagram                                                                 | Use Case Scenario (Detail)                                                                 |
|----------------------|----------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| **Mục đích chính**   | Cung cấp cái nhìn tổng quan về chức năng hệ thống và ai tương tác với nó.        | Cung cấp mô tả chi tiết về cách thức một chức năng cụ thể được thực hiện.                   |
| **Mức độ trừu tượng**| Cao - Chỉ hiển thị "What" (Cái gì) và "Who" (Ai).                                | Thấp - Mô tả "How" (Như thế nào), từng bước một.                                           |
| **Thành phần**       | Các hình hình học: Actor (hình que), Use Case (hình bầu dục), đường quan hệ.     | Văn bản có cấu trúc: Preconditions, Postconditions, Basic Flow, Alternative Flows, Exception Flows. |
| **Đối tượng hướng đến**| Tất cả stakeholders (cả kỹ thuật và không kỹ thuật) để thống nhất về phạm vi.   | Nhóm phát triển (BA, Dev, Tester) để hiểu rõ nghiệp vụ và xây dựng hệ thống.               |
| **Tính trực quan**   | Rất cao - Dễ dàng nắm bắt toàn cảnh.                                            | Thấp - Cần đọc và phân tích kỹ.                                                            |

---

## Ví Dụ Đặt Mua Hàng (Place Order)

### Use Case Diagram

```c++ 
     (Khách Hàng)
          |
          |
   +----------------+
   |  Đặt Mua Hàng  |<---------------------------+
   +----------------+                            |
          |                                      |
          | <<include>>                          | <<extend>>
          |                                      |
+------------------+                   +----------------------+
| Xác Minh Địa Chỉ |                   | Áp Dụng Mã Giảm Giá |
| Verify Address   |                   | Apply Coupon        |
+------------------+                   +----------------------+
```

### Use Case Scenario


| **Thành Phần**       | **Mô Tả** |
|-----------------------|-----------|
| **Use Case Name**     | Đặt Mua Hàng (Place Order) |
| **Actor**             | Khách hàng (Customer) |
| **Mô tả**             | Cho phép khách hàng đặt mua các sản phẩm trong giỏ hàng. |
| **Preconditions**     | 1. Khách hàng đã đăng nhập.<br>2. Giỏ hàng có ít nhất một sản phẩm. |
| **Postconditions**    | **Thành công:** Đơn hàng được tạo, trạng thái "Chờ thanh toán". |
| **Basic Flow**        | 1. Khách hàng nhấn nút **"Đặt Hàng"** từ giỏ hàng.<br>2. Hệ thống hiển thị trang xác nhận đơn hàng, bao gồm:<br>&nbsp;&nbsp;– Danh sách sản phẩm.<br>&nbsp;&nbsp;– Xác minh địa chỉ giao hàng và tính phí vận chuyển (`<<include>>`).<br>&nbsp;&nbsp;– Tính tổng tiền đơn hàng (`<<include>>`).<br>3. Khách hàng xem xét và nhấn **"Xác Nhận Đặt Hàng"**.<br>4. Hệ thống tạo đơn hàng, gửi email xác nhận (`<<include>>`).<br>5. Hệ thống hiển thị thông báo **"Đặt hàng thành công"**.<br>6. Use case kết thúc. |
| **Alternative Flows** | **AF1: Áp dụng mã giảm giá (Tại Bước 2)**<br>2.1. Khách hàng nhập mã giảm giá.<br>2.2. Hệ thống kiểm tra tính hợp lệ.<br>2.3. Nếu hợp lệ, cập nhật tổng tiền.<br>2.4. Nếu không hợp lệ, hiển thị thông báo lỗi.<br>2.5. Quay lại Bước 2.<br><br>**AF2: Chỉnh sửa địa chỉ giao hàng (Tại Bước 2)**<br>2.1. Khách hàng nhấn **"Thay đổi"** địa chỉ.<br>2.2. Hệ thống hiển thị popup chọn/thêm địa chỉ.<br>2.3. Khách hàng chọn địa chỉ mới.<br>2.4. Hệ thống xác minh & tính lại phí vận chuyển.<br>2.5. Quay lại Bước 2. |
| **Exception Flows**   | **EF1: Hết hàng (Tại Bước 4)**<br>4.1. Hệ thống phát hiện sản phẩm hết hàng.<br>4.2. Hủy đơn và báo lỗi: *"Sản phẩm [Tên SP] đã hết hàng"*. <br>4.3. Use case kết thúc thất bại. |

---

# Phần 3 – Sơ Đồ Hành Vi (Behavioral Diagrams)

---

## 3.1 Activity Diagrams

# Activity Diagram

**Activity Diagram (biểu đồ hoạt động)** là một loại biểu đồ **hành vi (behavior diagram)** trong UML — dùng để mô tả **luồng công việc (workflow) hoặc luồng điều khiển (control flow) giữa các hoạt động (activities)** trong một hệ thống.

Nói cách khác, **Activity Diagram thể hiện quá trình xử lý từng bước của một nghiệp vụ hoặc chức năng trong hệ thống.**

| Thành phần             | Ký hiệu                  | Ý nghĩa                                                            |
| ---------------------- | ------------------------ | ------------------------------------------------------------------ |
| **Initial Node**       | 🔵 (chấm đen)            | Điểm bắt đầu của luồng hoạt động                                   |
| **Activity / Action**  | ⬜ (hình chữ nhật bo góc) | Một hành động hoặc bước xử lý                                      |
| **Decision Node**      | ⬠ (hình thoi)            | Rẽ nhánh luồng dựa vào điều kiện                                   |
| **Merge Node**         | ⬠ (hình thoi)            | Hợp nhất các nhánh sau điều kiện                                   |
| **Fork Node**          | ————                     | Chia luồng thành các nhánh song song                               |
| **Join Node**          | ————                     | Hợp nhất các luồng song song                                       |
| **Final Node**         | ⭕ (vòng tròn kép)        | Kết thúc luồng hoạt động                                           |
| **Transition (Arrow)** | ➜                        | Biểu diễn luồng chuyển từ hoạt động này sang hoạt động khác        |
| **Swimlane**           | 🏊                       | Phân chia trách nhiệm (ví dụ: Người dùng, Hệ thống, Quản trị viên) |

![](https://circle.visual-paradigm.com/wp-content/uploads/2017/06/Activity-Diagram-ATM.png)

---

## Actions

- **Action** là bước hành động nhỏ nhất trong một **Activity**.
- Không thể chia nhỏ thêm trong cùng một sơ đồ.
- **Hình dạng:** hình chữ nhật bo góc.
- **Tên:** thường là động từ, ví dụ: `Process Order`, `Review Document`, `Checkout`.

**Cách hoạt động**

- Chỉ chạy khi **điều kiện đầu vào** thỏa mãn.
- Khi xong, kích hoạt **action tiếp theo**.
- Nếu có **exception**, có thể **bắt lỗi** hoặc **lan truyền ra ngoài**.

---

## Controls

- Là **nút điều khiển** trong Activity Diagram.  
- **Chức năng:** điều phối các luồng (flow) giữa các node khác.  
- Dùng để điều khiển **bắt đầu, kết thúc, phân nhánh, kết hợp, đồng bộ** luồng.

**Hoạt động cơ bản**
- **Initial Node:** token đặt ở đây khi Activity bắt đầu. 

![](https://www.uml-diagrams.org/activity-diagrams/activity-activity-initial.png)

- **Flow Final Node:** token tới đây → luồng kết thúc, token bị hủy. 

![](https://www.uml-diagrams.org/activity-diagrams/activity-flow-final.png)

- **Activity Final Node:** token tới đây → kết thúc toàn bộ Activity, hủy tất cả token.  

![](https://www.uml-diagrams.org/activity-diagrams/activity-activity-final.png)

- **Decision Node:** chọn **một luồng ra** dựa trên điều kiện (guard). 

![](https://www.uml-diagrams.org/activity-diagrams/decision-binary.png)
![](https://www.uml-diagrams.org/activity-diagrams/decision-ternary.png)


- **Merge Node:** gộp nhiều luồng thay thế → một luồng ra.  

![](https://www.uml-diagrams.org/activity-diagrams/activity-control-merge.png)

- **Fork Node:** nhân token ra nhiều luồng song song. 

![](https://www.uml-diagrams.org/activity-diagrams/activity-fork.png)

- **Join Node:** chờ tất cả luồng tới → kết hợp thành một luồng duy nhất.

![](https://www.uml-diagrams.org/activity-diagrams/activity-join.png)

---

##  Fork Node và Join Node

### 1. Fork Node (Chia luồng song song)
- **Chức năng:** Một luồng ra → nhiều luồng **chạy song song**.  
- **Token:** Token tới Fork sẽ **nhân bản** cho từng luồng ra.  
- **Ký hiệu UML:** một **thanh ngang** với **1 vào, nhiều ra**.  

![](https://sparxsystems.com/enterprise_architect_user_guide/17.1/images/activity-forkjoin2.png)

**Ví dụ:**  
Sau khi thanh toán xong trong Activity "Xử lý đơn hàng":  
- Gửi email xác nhận khách hàng  
- Cập nhật kho  
- Thông báo bộ phận vận chuyển  

→ 3 bước này **chạy cùng lúc** → dùng **Fork Node**.


---

### 2. Join Node (Kết hợp luồng song song)
- **Chức năng:** Nhiều luồng song song → hợp lại thành **một luồng duy nhất**.  
- **Token:** Chờ **tất cả token từ các luồng vào** tới → mới đi tiếp.  
- **Ký hiệu UML:** một **thanh ngang** với **nhiều vào, 1 ra**.  

![](https://sparxsystems.com/enterprise_architect_user_guide/17.1/images/activity-forkjoin1.png)

**Ví dụ:**  
Sau khi gửi email, cập nhật kho, và thông báo vận chuyển xong:  
- Hợp lại để cập nhật trạng thái đơn hàng hoàn tất → dùng **Join Node**.

---

## 3.2 Sequence Diagrams

# Sequence Diagrams

**Sequence Diagram** là loại biểu đồ tương tác phổ biến nhất trong UML, dùng để mô tả trình **tự trao đổi thông điệp** giữa các đối tượng (lifelines) theo thời gian.

Nó cho thấy **ai gọi ai, gọi khi nào, và phản hồi ra sao** trong một tiến trình hoặc use case.

| **Thành phần**                           | **Mô tả**                                                                                                                                        | **Ký hiệu (Notation)**                                   |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| **Lifeline**                             | Đại diện cho một đối tượng hoặc thực thể tham gia vào tương tác. Hiển thị bằng hình chữ nhật (đầu) và đường thẳng đứng (thân) thể hiện vòng đời. | ▭────────── (đường thẳng đứng dưới tên đối tượng)        |
| **Message**                              | Mũi tên thể hiện thông điệp gửi giữa các lifelines. Có thể là gọi hàm, gửi tín hiệu, hoặc phản hồi.                                              | → (synchronous), (asynchronous), ↩ (return)            |
| **Execution Specification (Activation)** | Hình chữ nhật hẹp trên lifeline, thể hiện thời gian đối tượng đang xử lý hành động hoặc chờ phản hồi.                                            | ▯ (hình chữ nhật hẹp trên lifeline)                      |
| **Occurrence**                           | Thời điểm một sự kiện xảy ra, như bắt đầu hoặc kết thúc của một message.                                                                         | • (điểm trên lifeline, không có ký hiệu riêng trong UML) |
| **Destruction Occurrence**               | Dấu "X" ở cuối lifeline, biểu thị đối tượng bị hủy hoặc kết thúc tồn tại.                                                                        | ✕ (dấu X ở cuối lifeline)                                |
| **State Invariant (ít dùng)**                      | Ràng buộc trạng thái của đối tượng tại thời điểm cụ thể (ví dụ: `status = Completed`).                                                           | `{constraint}` hoặc trạng thái trong ô nhỏ trên lifeline |
| **Combined Fragment**                    | Khối logic gồm điều kiện `alt`, vòng lặp `loop`, hoặc tùy chọn `opt`, tương tự if–else/for/while.                                                | Khung chữ nhật có nhãn `alt`, `loop`, `opt`, ...         |
| **Interaction Use**                      | Tái sử dụng một biểu đồ tương tác khác (gọi là `ref`), giúp biểu đồ gọn hơn.                                                                     | Khung chữ nhật có nhãn `ref`                             |

![](https://www.uml-diagrams.org/sequence-diagrams/sequence-diagram-overview.png)

---

## Message

**Message (Thông điệp)** trong UML Sequence Diagram biểu diễn một hành động giao tiếp giữa **các đối tượng (lifeline)** trong một hệ thống.

```c++
User -> System: login(username, password)
System --> User: return success
```

| Loại                    | Ký hiệu UML                                                                    | Giải thích dễ hiểu                                          | Ví dụ thực tế                                             |
| ----------------------- | ------------------------------------------------------------------------------ | ----------------------------------------------------------- | --------------------------------------------------------- |
| **Synchronous Call**    | Mũi tên **đầu kín (filled)**                                                   | Gọi hàm **chờ kết quả**, giống như `function()` trong code. | `User -> System: login()` rồi đợi phản hồi.               |
| **Asynchronous Call**   | Mũi tên **đầu mở (open)**                                                      | Gửi xong **không chờ kết quả**, chạy tiếp.                  | `Server -> Logger: logEvent()` và tiếp tục làm việc khác. |
| **Asynchronous Signal (ít dùng)** | Giống Asynchronous Call, nhưng thể hiện **tín hiệu (signal)** thay vì gọi hàm. | `Sensor -> Alarm: signal()`.                                |                                                           |
| **Create Message (ít dùng)**      | Đường nét **gạch đứt** đến **lifeline mới xuất hiện**                          | Dùng để **tạo đối tượng**.                                  | `System ..> Account: create()`.                           |
| **Delete Message (ít dùng)**      | Gửi để **xóa đối tượng**, lifeline kết thúc bằng chữ **X**                     | `System -> Account: «destroy»`.                             |                                                           |
| **Reply Message (ít dùng)**       | Đường **gạch đứt** với mũi tên **mở**                                          | Phản hồi từ lời gọi đồng bộ (synchronous).                  | `System --> User: return success`.                        |

![](https://help.bizzdesign.com/resources/Storage/horizzon-help/specifying-the-type-of-a-message-in-a-uml-sequence-diagram/worddav669df1d6e1ac5266ad5312a65db0622d.png)

---

## Combined Fragment

**Combined Fragment** là thành phần trong **UML Sequence Diagram** dùng để mô tả **cấu trúc điều khiển** (rẽ nhánh, lặp, song song, điều kiện, v.v.).  
Nó giúp biểu đồ tuần tự ngắn gọn và thể hiện logic chương trình rõ ràng hơn.

Một Combined Fragment gồm:
- **Interaction Operator**: loại hành vi (alt, loop, par, …)
- **Interaction Operand**: phần nội dung (các thông điệp, hành động)

| Operator | Nghĩa | Giải thích dễ hiểu | Ví dụ |
|-----------|--------|--------------------|--------|
| **alt** | Alternative | Rẽ nhánh `if / else` | Nếu `balance > 0` → `accept()`, ngược lại → `reject()` |
| **opt** | Option | Tùy chọn, giống `if` (có thể không chạy) | Nếu `no errors` → `postComment()` |
| **loop** | Loop | Lặp lại hành vi (giống `for`, `while`) | Lặp `processItem()` 5–10 lần nếu `[size > 0]` |
| **break (ít dùng)** | Break | Thoát khỏi phần còn lại của biểu đồ | Nếu `[y > 0]` → dừng xử lý |
| **par (ít dùng)** | Parallel | Thực hiện song song hoặc xen kẽ | Tìm kiếm `Google`, `Bing`, `Ask` cùng lúc |
| **strict (ít dùng)** | Strict sequencing | Tuần tự nghiêm ngặt | Gọi `A()` → `B()` → `C()` theo đúng thứ tự |
| **seq (ít dùng)** | Weak sequencing | Tuần tự yếu, linh hoạt giữa các lifeline | `Google` song song `Bing`, nhưng `Bing` trước `Yahoo` |
| **critical (ít dùng)** | Critical region | Vùng độc quyền, không xen kẽ tiến trình khác | `add()` và `remove()` chạy song song, nhưng mỗi cái phải hoàn tất trước khi xen |
| **ignore (ít dùng)** | Ignore | Bỏ qua các message không quan trọng | Bỏ qua `get()` và `set()` |
| **consider (ít dùng)** | Consider | Chỉ xét một số message, bỏ qua phần khác | Chỉ xét `add()` và `remove()` |
| **assert (ít dùng)** | Assertion | Chỉ cho phép các hành vi trong khối là hợp lệ | `commit()` phải xảy ra |
| **neg (ít dùng)** | Negative | Mô tả tình huống lỗi / thất bại | Nhận `timeout` → hệ thống thất bại |

### Operator alt

- Thể hiện các lựa chọn tương tự như câu lệnh `if...else` trong lập trình.  
- Mỗi nhánh trong `alt` có một **điều kiện (guard condition)** xác định khi nào nó được thực hiện.  
- Dạng ký hiệu thường gặp là **Decision Node (hình thoi)** với các nhánh được ghi điều kiện bên cạnh.

![](https://www.softwareideas.net/i/DirectImage/3244/alt-fragment)

### Operator opt

- Tương tự như câu lệnh `if` trong lập trình (không có `else`).  
- Thường được dùng để biểu diễn **một hành động tùy chọn** hoặc **trường hợp đặc biệt**.  
- Chỉ có **một nhánh duy nhất** với **điều kiện bảo vệ (guard condition)**.  

![](https://www.softwareideas.net/i/DirectImage/3245/opt-fragment)

### Operator loop

- Tương tự như `while` hoặc `for` trong lập trình.  
- Luồng điều khiển sẽ **quay lại điểm bắt đầu** của hành động khi điều kiện vẫn còn đúng.  
- Khi điều kiện sai, quá trình lặp **kết thúc** và chuyển sang hành động tiếp theo.

![](https://i.sstatic.net/xJG1g.png)

---

## 3.3 State Machine Diagram

# State Machine Diagram (Statechart Diagram)

**State Machine Diagram** (hoặc **Statechart Diagram**) là **behavioral diagram** mô tả **sự thay đổi trạng thái của một đối tượng** khi có các **sự kiện (events)** xảy ra.

| Loại | Giải thích | Ứng dụng |
|------|-------------|-----------|
| **Behavioral State Machine** | Mô tả hành vi của một đối tượng thông qua trạng thái và chuyển tiếp. | ATM, đơn hàng, luồng actor |
| **Protocol State Machine** | Mô tả quy tắc giao tiếp giữa các đối tượng. | Quy tắc API, protocol giao tiếp |

---

**Thành phần chính**

| Thành phần | Ký hiệu / Mô tả |
|-------------|------------------|
| **State** | Trạng thái của đối tượng (Idle, Processing, Completed, …) |
| **Transition** | Mũi tên chỉ ra sự chuyển đổi giữa các trạng thái |
| **Event / Trigger** | Sự kiện gây ra chuyển đổi |
| **Guard [ ]** | Điều kiện để chuyển đổi xảy ra |
| **Action / Effect** | Hành động được thực hiện khi chuyển đổi |
| **Initial State (●)** | Trạng thái bắt đầu |
| **Final State (◎)** | Trạng thái kết thúc |
| **Composite State** | Trạng thái chứa các trạng thái con |
| **Submachine State** | Tham chiếu đến một state machine khác |

![](https://guides.visual-paradigm.com/wp-content/uploads/2023/09/state-machine-diagram-explained.png)

**Các loại Pseudostate**

| Loại | Ký hiệu | Ý nghĩa |
|------|----------|----------|
| **Initial** | ● | Bắt đầu |
| **Final** | ◎ | Kết thúc |
| **Choice** | ◆ | Rẽ nhánh theo điều kiện động |
| **Junction** | ● nhỏ | Nối nhiều nhánh thành một |
| **Fork / Join** | ▬ | Chia hoặc hợp luồng song song |
| **Entry / Exit Point** | ⊙ / ⊗ | Điểm vào hoặc ra của composite state |
| **Shallow History (H)** | H | Ghi nhớ trạng thái con cuối |
| **Deep History (H\*)** | H* | Ghi nhớ toàn bộ cấu hình trước đó |

![](https://d2slcw3kip6qmk.cloudfront.net/marketing/pages/chart/UML-state-diagram-tutorial/state_diagram_scheduling_system-740x860.pngg)

---

# Phần 4 – Sơ Đồ Cấu Trúc (Structural Diagrams)

---

## 4.1 Class Diagram và Method Descriptions

# Class diagram

**Class diagram (sơ đồ lớp)** là một **sơ đồ UML** mô tả **cấu trúc của hệ thống** thông qua các **lớp (class)**, **thuộc tính (attributes)**, **phương thức (methods)**, và **mối quan hệ** giữa các lớp.

![](https://www.uml-diagrams.org/class-diagrams/class-diagram-implementation-elements.png)

## **1. Class (Lớp)**

* Là **mô hình tổng quát (template)** mô tả một **đối tượng (object)**.
* Gồm:
  * **Tên lớp**
  * **Thuộc tính (attributes / properties)**
  * **Phương thức (methods / operations)**
* Ví dụ:

  ```plaintext
  +--------------------+
  |    Student         |
  +--------------------+
  | - name: String     |
  | - id: int          |
  +--------------------+
  | + enroll(): void   |
  | + study(): void    |
  +--------------------+
  ```

---

## **2. Interface**

* Là **bộ khung (contract)** định nghĩa **các hành vi (methods)** mà lớp **phải triển khai (implement)**.
* Không chứa dữ liệu cụ thể, chỉ chứa khai báo.
* Dùng để tạo tính **đa hình (polymorphism)**.

![](https://www.uml-diagrams.org/class-diagrams/class-interface-compartments.png)


---

## **3. Data Type**

* Là **kiểu dữ liệu cơ bản hoặc tự định nghĩa** dùng trong các thuộc tính/lớp.
* Ví dụ: `int`, `string`, `float`, hoặc kiểu tự tạo như `Date`, `Address`.

---

## **4. Property (Attribute)**

* Là **thuộc tính / biến dữ liệu** của lớp.
* Mô tả **đặc điểm** của đối tượng.
* Ví dụ: `name`, `age`, `price`, `balance`.

---

## **5. Operation (Method)**

* Là **hành vi hoặc chức năng** mà lớp có thể thực hiện.
* Gồm **tên**, **tham số**, **kiểu trả về**.
* Ví dụ:

```plaintext
+ withdraw(amount: double): void
```

---

## **6. Multiplicity**

* Mô tả **số lượng đối tượng** trong một mối quan hệ.
* Ví dụ:

  * `1` → một đối tượng duy nhất
  * `0..1` → có thể có hoặc không
  * `1..*` → ít nhất một
  * `*` → nhiều (không giới hạn)
* Ví dụ: Một `Department` có `1..* Employee`.

---

## **7. Visibility**

* Chỉ rõ **mức độ truy cập (access modifier)** của thuộc tính hoặc phương thức.
  | Ký hiệu | Loại | Ý nghĩa |
  |----------|--------|----------|
  | `+` | public | Truy cập được ở mọi nơi |
  | `-` | private | Chỉ trong cùng lớp |
  | `#` | protected | Trong lớp và lớp con |
  | `~` | package | Trong cùng gói |

![](https://www.uml-diagrams.org/class-diagrams/class-operation-visibility.png)

---

## **8. Constraint (Ràng buộc)**

* Mô tả **điều kiện hoặc quy tắc** phải thỏa mãn.
* Viết trong dấu ngoặc nhọn `{}`.

![](https://www.uml-diagrams.org/class-diagrams/class-constraint-attribute.png)

---

## **9. Object**

* Là **thể hiện cụ thể (instance)** của một lớp.
* Biểu diễn trong UML bằng tên:

  ```
  student1: Student
  ```

---

## **10. Generalization (Kế thừa – inheritance)**

* Mô tả mối quan hệ **is-a** giữa lớp cha và lớp con.
* Biểu diễn bằng **mũi tên rỗng hướng lên trên**.
* Ví dụ:

  ```
  Animal ⟵ Dog
  Animal ⟵ Cat
  ```

---

## **11. Dependency (Phụ thuộc)**

* Một lớp **phụ thuộc tạm thời** vào lớp khác (dùng trong method, truyền tham số,...).
* Biểu diễn bằng **mũi tên nét đứt →**.
* Ví dụ:

  * `Student → Course` (Student dùng Course trong hàm `register()`)

---

## **12. Abstraction**

* Là khái niệm trừu tượng hóa (abstract class / interface).
* Dùng để **định nghĩa khung hành vi** mà lớp con cụ thể sẽ **thực thi**.
* Ký hiệu bằng chữ nghiêng hoặc `{abstract}`.
  Ví dụ:

  ```
  abstract class Shape
  + area(): double
  ```

---

## **13. Nested Classifiers (Lớp lồng nhau)**

* Một lớp được **định nghĩa bên trong lớp khác**.
* Dùng để nhóm các lớp có liên quan chặt chẽ.
* Ví dụ:

  ```plaintext
  class University {
      class Department {
      }
  }
  ```

## **14. Association – Aggregation – Composition**

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhSejrYsJxJYXxrG9iDCPCAaT6hffYlrJjXeUPy7G_RvnthyAaAv31n4aLRRDS8twoiRwWK-Otp1Fwu9N3TzqGx8RqPUFQUbd-PPsviXqH5z3wSc59QbaOE9fAD81_W73lLWPtAuNJ8PDHi/s1600/Association,+Composition+UML.JPG)

| **Tiêu chí**                   | **Association (Kết hợp)**                                                                                                   | **Aggregation (Tập hợp)**                                                                                      | **Composition (Thành phần)**                                                                            |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Định nghĩa**                 | Là **mối quan hệ tổng quát** giữa hai lớp, biểu thị rằng các đối tượng của lớp này **liên quan** đến đối tượng của lớp kia. | Là **mối quan hệ "whole–part" (toàn thể–bộ phận)**, trong đó **các phần có thể tồn tại độc lập** với toàn thể. | Là **mối quan hệ "whole–part" mạnh hơn**, trong đó **các phần không thể tồn tại độc lập** với toàn thể. |
| **Độ chặt (mức độ phụ thuộc)** | Quan hệ **lỏng lẻo**, chỉ là sự kết nối logic.                                                                              | Quan hệ **trung bình**, có liên kết "has-a" nhưng vẫn độc lập.                                                 | Quan hệ **chặt chẽ**, ràng buộc sinh–tử ("owns-a" hoặc "contains-a").                                   |
| **Ký hiệu UML**                | Đường kẻ đơn giản giữa hai lớp.                                                                                             | Đường kẻ có **hình thoi rỗng (◇)** ở đầu lớp "toàn thể".                                                       | Đường kẻ có **hình thoi đặc (◆)** ở đầu lớp "toàn thể".                                                 |
| **Vòng đời (lifecycle)**       | Các đối tượng tồn tại **độc lập** nhau.                                                                                     | "Phần" có thể tồn tại **độc lập** với "toàn thể".                                                              | "Phần" **phụ thuộc hoàn toàn** vào "toàn thể"; nếu "toàn thể" bị hủy, "phần" cũng bị hủy.               |
| **Ví dụ thực tế**              | `Student` ↔ `Course` – Sinh viên có thể học nhiều khóa, khóa có nhiều sinh viên.                                            | `Department` ◇– `Teacher` – Giáo viên thuộc một khoa, nhưng giáo viên vẫn tồn tại nếu khoa bị xóa.             | `House` ◆– `Room` – Phòng không thể tồn tại nếu căn nhà bị phá.                                         |
| **Loại quan hệ**               | "Uses" hoặc "knows"                                                                                                         | "Has-a" (sở hữu yếu)                                                                                           | "Owns-a" (sở hữu mạnh)                                                                                  |
| **Tính kế thừa**               | Không có quan hệ sở hữu                                                                                                     | Có quan hệ sở hữu một phần                                                                                     | Có quan hệ sở hữu hoàn toàn                                                                             |

---

# Method descriptions

**Method descriptions** nghĩa là **mô tả chi tiết cho từng phương thức (method)** trong các lớp của sơ đồ lớp (class diagram).
Nói cách khác, khi anh đã có **class diagram** — tức là đã biết mỗi lớp có những **thuộc tính (attributes)** và **phương thức (methods)** nào — thì phần **method descriptions** chính là **phần tài liệu hóa chi tiết** cách mà từng phương thức hoạt động.

---

## 4.2 Component Diagrams

# Component Diagrams

**Component Diagram** (Sơ đồ thành phần) dùng để mô tả **cấu trúc cấp cao** của hệ thống phần mềm — tức là **hệ thống được tạo thành từ những thành phần nào**, và **các thành phần đó tương tác ra sao**.

![](https://www.uml-diagrams.org/component-diagrams/component-diagram-overview.png)

| **Mục**                           | **Ý nghĩa chính**                                                   |
| --------------------------------- | ------------------------------------------------------------------- |
| **Component Diagram**             | Mô tả cách chia hệ thống thành các module lớn và quan hệ giữa chúng |
| **Component**                     | Một module phần mềm độc lập                                         |
| **Provided / Required Interface** | Các dịch vụ được cung cấp hoặc yêu cầu giữa các component           |
| **Port**                          | Điểm giao tiếp giữa component và bên ngoài                          |
| **Connector**                     | Liên kết giữa các component                                         |
| **Component Realization**         | Lớp hiện thực hóa component đó                                      |

--- 

## Component

* **Component**: module phần mềm độc lập, đóng gói, có thể thay thế.
* **Behavior** xác định qua **provided interface** (cung cấp) và **required interface** (yêu cầu).
* Hiện thực bởi **artifact** (file `.jar`, `.dll`, `.py`…).

![](https://ducmanhphan.github.io/img/UML/interfaces/provided-&&-required-interfaces.png)

### Interfaces

| Loại     | Ý nghĩa                     | Notation |
| -------- | --------------------------- | -------- |
| Provided | Cung cấp cho component khác | Lollipop |
| Required | Yêu cầu từ component khác   | Socket   |


### Stereotypes tiêu chuẩn

* `«BuildComponent»`: cho phát triển, version
* `«Entity»`: persistent data
* `«Service»`: chức năng stateless
* `«Specification»`: chỉ định domain, không hiện thực
* `«Realization»`: class hiện thực specification
* `«Process»`: transaction-based
* `«Subsystem»`: thành phần lớn, phân cấp hệ thống


### Nguyên tắc

* **Encapsulation:** ẩn chi tiết, chỉ interface được nhìn thấy
* **Reusability:** có thể tái sử dụng
* **Replaceability:** thay thế component tương thích không ảnh hưởng hệ thống
* **Deployment:** triển khai qua artifact

--- 

## Connector

* **Connector** là **liên kết** giữa hai hoặc nhiều **instances** (thực thể) trong một **structured classifier** (ví dụ component).
* Connector cho phép **giao tiếp hoặc chuyển tín hiệu** giữa các instance.
* Khác với association (kết nối giữa class), connector **kết nối các instance cụ thể**, không phải mọi instance của class.
* Có **hai loại connector chính**:

![](https://media.licdn.com/dms/image/v2/C4D12AQHkE0haKnqpBQ/article-inline_image-shrink_1000_1488/article-inline_image-shrink_1000_1488/0/1649921932031?e=2147483647&v=beta&t=04OlHI1w-oleZ4IfvfeET34cOcMWyzeB5Jnr3RQYitc)

### Assembly Connector

* Kết nối giữa **hai hoặc nhiều part/port**.
* Một part cung cấp **service** mà part khác **sử dụng**.
* Notation: ball-and-socket cho simple ports, hoặc connector line cho n-ary connectors.
* Cho phép **thay thế component** nếu interfaces tương thích.


### Delegation Connector

* Kết nối từ **external port của component** đến **realization (hiện thực) của behavior**.
* Chuyển tiếp **signal/operation** đến port hoặc part bên trong.
* Mô hình hóa **hierarchical decomposition**, tức services bên ngoài có thể được thực hiện bởi component nested nhiều tầng.
* Notation: connector từ **delegating port** đến **target port/part**.

---

## 4.3 Deployment Diagrams

# Deployment Diagrams Overview

* Là **structure diagram** mô tả **kiến trúc hệ thống** dưới dạng **triển khai phần mềm (artifacts) lên các deployment targets** (phần cứng hoặc môi trường thực thi).
* Giúp hình dung **cách phần mềm được phân phối và chạy trên các node**.

![](https://www.uml-diagrams.org/examples/deployment-example-clusters.png)

## **Các thành phần chính**

| Thành phần                   | Ý nghĩa                                                                                             |
| ---------------------------- | --------------------------------------------------------------------------------------------------- |
| **Artifact**                 | Phần tử vật lý, kết quả của quá trình phát triển: file thực thi, thư viện, database schema, config… |
| **Deployment Target / Node** | Mục tiêu triển khai: máy chủ, client, môi trường ảo…                                                |
| **Component**                | Module phần mềm, được **manifest (hiện thực) bởi artifact**.                                        |
| **Communication Path**       | Kết nối giữa các node, cho phép giao tiếp mạng hoặc trao đổi dữ liệu.                               |

## **Các loại Deployment Diagram**

1. **Specification Level (Type Level)**

   * Mô tả tổng quan **triển khai artifact lên target**, **không nêu cụ thể các instance**.

2. **Instance Level**

   * Mô tả **triển khai các instance cụ thể** của artifact lên các node cụ thể.
   * Dùng để phân biệt **môi trường development, staging, production**.

3. **Manifestation Diagram**

   * Thể hiện **component được hiện thực bởi artifact**.
   * UML 2.x cho phép thể hiện bằng **component diagram hoặc deployment diagram**.

4. **Network Architecture**

   * Hiển thị **mạng lưới logical/physical** của hệ thống, với hoặc không với artifacts.

---

# Phần 5 – Kiểm Thử

---

## 5.1 Use-case Testing

# Use-case testing

**Use-case testing** là kỹ thuật kiểm thử **dựa trên các Use Case của hệ thống**
→ Mỗi **Use Case** (ví dụ: "Đăng nhập", "Đặt lịch học", "Gửi phản hồi") được chuyển thành **một tập test case** mô tả rõ:

* Luồng chính (main flow)
* Luồng thay thế (alternate flow)
* Các đầu vào/đầu ra kỳ vọng (input/output)
* Điều kiện tiên quyết và hậu điều kiện (pre-/post-condition)

Mục tiêu: đảm bảo hệ thống thực hiện **đúng hành vi của người dùng trong từng tình huống nghiệp vụ**.

---

## Cách viết Test Report từ Use Case

![](https://browserstack.wpenginepowered.com/wp-content/uploads/2024/11/Test-Case-Example.png)


1. **Test Case ID** Mã định danh duy nhất của mỗi trường hợp kiểm thử, giúp phân biệt và truy vết dễ dàng.

2. **Test Case Description** Mô tả ngắn gọn mục tiêu hoặc chức năng cần được kiểm thử.

3. **Pre-conditions** Các điều kiện tiên quyết phải được đáp ứng trước khi bắt đầu thực hiện kiểm thử.

4. **Steps** Danh sách các bước cụ thể mà người kiểm thử cần thực hiện để kiểm tra chức năng.

5. **Expected Result** Kết quả dự kiến hệ thống phải hiển thị hoặc thực hiện nếu hoạt động đúng.

6. **Actual Result** Kết quả thực tế thu được khi thực hiện kiểm thử.

7. **Status** Trạng thái của test case: **Pass** nếu kết quả thực tế trùng khớp với kết quả mong đợi, **Fail** nếu không.

8. **Comments** *(tùy chọn)* Ghi chú bổ sung về vấn đề gặp phải, môi trường thử nghiệm, hoặc đề xuất cải tiến.
