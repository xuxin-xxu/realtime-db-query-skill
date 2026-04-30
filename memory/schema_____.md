# Schema:      (Oracle)

**用户:** `jaenergy`
**发现时间:** `2026-04-30 09:42:43`

## 表清单

| 表名 | 行数 | 注释 |
|------|------|------|
| JAE_MONTHLY_POWER_FEE | 3126799 |  |
| JAE_PS_BOM | 1001822 |  |
| JAE_MONTHLY_POWER_COMPARE | 100872 |  |
| JAE_PS | 100668 | 并网电站全量表 |
| JAE_CITIC_OWNER_INFO | 32939 |  |
| JAE_CITIC_PS_BASE_INFO | 32939 |  |
| JAE_CITIC_PS | 32939 |  |
| JAE_CITIC_PS_SCOPE | 32939 |  |
| JAE_DAILY_POWER_ABNORMAL | 2187 |  |
| JAE_RENTAL_PRICE_PROVINCE | 994 | 各省租金 |
| JAE_OA_COMPANY_ENTITY | 376 |  |
| JAE_POWER_PRICE_PROVINCE | 44 |  |
| JAE_PROVINCE | 34 |  |
| EMP | 14 |  |
| DEPT | 8 |  |
| JAE_RENTAL_PRICE_PROVINCE_ERR$ | 1 | DML Error Logging table for "JAE_RENTAL_PRICE_PROVINCE" |

## 表结构详情

### JAE_MONTHLY_POWER_FEE

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| STATIONNO | VARCHAR2(200) | Y |  |
| MEDIUMID | VARCHAR2(44) | Y |  |
| STATION_COUNT_PER_CARD | NUMBER(22) | Y |  |
| POWERMONTH | VARCHAR2(40) | Y |  |
| POWER_AMOUNT | NUMBER(22) | Y |  |
| PRICE | NUMBER(22) | Y |  |
| POWER_FEE_THEORETICAL | NUMBER(22) | Y |  |
| CARD_POWER_SUM | NUMBER(22) | Y |  |
| CARD_TOTAL_RECEIPT | NUMBER(22) | Y |  |
| ALLOCATED_FEE | NUMBER(22) | Y |  |
| CLOSING_BALANCE | NUMBER(22) | Y |  |
| CARD_TOTAL_DEDUCT | NUMBER(22) | Y |  |

### JAE_PS_BOM

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| DIPATCHTIME_CONFIRM | VARCHAR2(200) | Y | 派工确认日期 |
| STATIONNO | VARCHAR2(50) | Y |  |
| INTENTIONSTATE | NUMBER(38) | Y | 电站状态 |
| AGENT | VARCHAR2(100) | Y | 代理商 |
| MATERIALCODE | VARCHAR2(200) | Y | 物料编码 |
| MATERIALNAME | VARCHAR2(200) | Y | 物料名称 |
| PROPERTYOWNER | VARCHAR2(100) | Y | 产权方 |
| ITEMGROUP | VARCHAR2(100) | Y | 物料组 |
| EQUIPMENTNUMBER | VARCHAR2(200) | Y | 设备编号 |
| COLLECTORNUMBER | VARCHAR2(100) | Y | 采集器编号 |
| UNIT | VARCHAR2(10) | Y | 单位 |
| DESIGNQUANTITY | NUMBER(38) | Y | 设计数量 |
| ENGINEERINGQUANTITY | NUMBER(38) | Y | 工程数量 |
| UNITPRICE | NUMBER(20) | Y | 单价 |
| POWER | NUMBER(38) | Y | 功率（w） |
| DIPATCHTIME | VARCHAR2(200) | Y | 派工日期 |
| ENDCHECKTIME | VARCHAR2(10) | Y | 并网审核通过日期 |

### JAE_MONTHLY_POWER_COMPARE

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| STATION_NUMBER | VARCHAR2(256) | Y |  |
| CURRENT_MONTH | VARCHAR2(40) | Y |  |
| CURRENT_SUM | NUMBER(22) | Y |  |
| RECORD_MONTH | VARCHAR2(40) | Y |  |
| RECORD_AMOUNT | NUMBER(22) | Y |  |
| TOTAL_POWER | NUMBER(22) | Y |  |
| LAST_ACTIVE_DATE | NUMBER(22) | Y |  |

### JAE_PS
**注释:** 并网电站全量表

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| ORDERID | NUMBER(38) | Y |  |
| STATIONNO | VARCHAR2(200) | Y |  |
| HOUSEHOLDER_NAME | VARCHAR2(300) | Y |  |
| HOUSEHOLDER_ID | VARCHAR2(100) | Y |  |
| HOUSEHOLDER_PHONE | VARCHAR2(200) | Y |  |
| PROVINCE | VARCHAR2(100) | Y |  |
| CITY | VARCHAR2(100) | Y |  |
| DISTRICT | VARCHAR2(100) | Y |  |
| TOWN | VARCHAR2(100) | Y |  |
| PSADDRESS | VARCHAR2(1900) | Y |  |
| LATITUDE | VARCHAR2(255) | Y |  |
| LONGITUDE | VARCHAR2(255) | Y |  |
| COLLECTIONTYPE | VARCHAR2(40) | Y |  |
| PRODUCT_NAME | VARCHAR2(40) | Y |  |
| BUSINESS_TYPE | VARCHAR2(40) | Y |  |
| MERGE_FILING_TYPE | VARCHAR2(40) | Y |  |
| PS_TYPE | VARCHAR2(50) | Y |  |
| PROJECT_COMPANY_NAME | VARCHAR2(100) | Y |  |
| EPC | VARCHAR2(255) | Y |  |
| DEVELOPER_CODE | VARCHAR2(255) | Y |  |
| DEVELOPER_NAME | VARCHAR2(100) | Y |  |
| SERVICE_PROVIDER_CODE | VARCHAR2(255) | Y |  |
| SERVICE_PROVIDER_NAME | VARCHAR2(100) | Y |  |
| AGENT_CODE | VARCHAR2(255) | Y |  |
| AGENT_NAME | VARCHAR2(100) | Y |  |
| AGENT_LECAL | VARCHAR2(50) | Y |  |
| AGENT_PHONE | VARCHAR2(50) | Y |  |
| AGENT_LICENSE | VARCHAR2(100) | Y |  |
| AGENT_ADDR | VARCHAR2(400) | Y |  |
| PS_STATE | VARCHAR2(40) | Y |  |
| POWER_ACCOUNT | VARCHAR2(200) | Y |  |
| FILING_CERT_CODE | VARCHAR2(255) | Y |  |
| COSIGNER_NAME | VARCHAR2(100) | Y |  |
| COSIGNER_ID | VARCHAR2(50) | Y |  |
| COSIGNER_PHONE | VARCHAR2(50) | Y |  |
| RENT_SHARE_BANK_NAME | VARCHAR2(300) | Y |  |
| DESIGN_SCHEME | VARCHAR2(4000) | Y |  |
| DESIGN_MODULE_TOTAL_PIECES | NUMBER(22) | Y |  |
| DESIGN_TOTAL_CAPACITY | NUMBER(22) | Y |  |
| SPEC_SOLUTION_TYPE | VARCHAR2(100) | Y |  |
| SPEC_SOLUTION_PIECES | NUMBER(38) | Y |  |
| INVERTER_COUNT | NUMBER(22) | Y |  |
| CONTRACT_SIGN_TYPE | VARCHAR2(40) | Y |  |
| FIRSTSTAGE_YEARCOUNT | NUMBER(22) | Y |  |
| FIRSTSTAGE_SHAREMONEY | NUMBER(22) | Y |  |
| SECONDSTAGE_YEARCOUNT | NUMBER(22) | Y |  |
| SECONDSTAGE_SHAREMONEY | NUMBER(22) | Y |  |
| THIRDSTAGE_YEARCOUNT | NUMBER(22) | Y |  |
| THIRDSTAGE_SHAREMONEY | NUMBER(22) | Y |  |
| BUSINESS_CREATE_DATE | VARCHAR2(20) | Y |  |
| SURVEY_FINISH_DATE | VARCHAR2(20) | Y |  |
| CONTRACT_CREATE_DATE | VARCHAR2(20) | Y |  |
| CONTRACT_MERGE_DATE | VARCHAR2(20) | Y |  |
| FILING_SUBMIT_DATE | VARCHAR2(20) | Y |  |
| BUSINESS_REVIEW_FINISH_DATE | VARCHAR2(20) | Y |  |
| TECH_REVIEW_FINISH_DATE | VARCHAR2(20) | Y |  |
| FILING_REVIEW_PASSED_DATE | VARCHAR2(20) | Y |  |
| FULL_DELIVER_DATE | VARCHAR2(20) | Y |  |
| DIPATCH_DATE | VARCHAR2(20) | Y |  |
| COMPLETE_SUBMIT_DATE | VARCHAR2(20) | Y |  |
| COMPLETE_CHECK_DATE | VARCHAR2(20) | Y |  |
| MERGE_APPLY_DATE | VARCHAR2(20) | Y |  |
| MERGE_BUSSINESS_REVIEW_DATE | VARCHAR2(20) | Y |  |
| MERGE_ENGINEERING_REVIEW_DATE | VARCHAR2(20) | Y |  |
| MERGE_REVIEW_PASS_DATE | VARCHAR2(20) | Y |  |
| COMPLETE_DATE | VARCHAR2(20) | Y |  |
| FIRST_POWER_DATE | VARCHAR2(20) | Y |  |
| CONTRACT_SIGN_DATE | VARCHAR2(20) | Y |  |
| BUSINESS_OPPT_NO | VARCHAR2(50) | Y |  |
| BUSINESS_OPPT_STATUS | VARCHAR2(40) | Y |  |
| RENT_SHARE_BANK_ACCOUNT_NAME | VARCHAR2(100) | Y |  |
| RENT_SHARE_BANK_ACCOUNT_NUM | VARCHAR2(100) | Y |  |
| RENT_SHARE_BANK_CODE | VARCHAR2(200) | Y |  |
| GRID_EARNING_BANK_ACCOUNT_NUM | VARCHAR2(100) | Y |  |
| GRID_EARNING_BANK_NAME | VARCHAR2(255) | Y |  |
| GRID_EARNING_BANK_ACCOUNT_NAME | VARCHAR2(255) | Y |  |
| DEDUCTION_BANK_ACCOUNT_NAME | VARCHAR2(100) | Y |  |
| DEDUCTION_BANK_ACCOUNT_NUM | VARCHAR2(50) | Y |  |
| DEDUCTION_BANK_NAME | VARCHAR2(40) | Y |  |
| MODULE_TOTAL_PIECES | NUMBER(38) | Y |  |
| MODULE_POWER | NUMBER(38) | Y |  |
| TOTAL_CAPACITY | NUMBER(38) | Y |  |
| CONTRACT_SIGN_STATUS | VARCHAR2(20) | Y |  |
| CONTRACT_SIGN_SECONDPART | VARCHAR2(200) | Y |  |
| CONTRACT_FIRST_EFFECTIVE_DATE | VARCHAR2(200) | Y |  |
| BIRTHDAY | VARCHAR2(30) | Y |  |
| OWNWER_SIGN_AGE | VARCHAR2(20) | Y |  |
| PROVINCE_CODE | VARCHAR2(10) | Y |  |
| CITY_CODE | VARCHAR2(10) | Y |  |
| DISTRICT_CODE | VARCHAR2(10) | Y |  |
| TOWN_CODE | VARCHAR2(10) | Y |  |
| PROJCOMP_BANK_ACCOUNT | VARCHAR2(150) | Y |  |
| PROJCOMP_BANK_NAME | VARCHAR2(150) | Y |  |
| INCOME_START_DATE | VARCHAR2(10) | Y |  |
| TAG_STATUS | VARCHAR2(10) | Y |  |

### JAE_CITIC_OWNER_INFO

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| STATION_NO | VARCHAR2(200) | Y |  |
| OWNER_NAME | VARCHAR2(300) | Y |  |
| OWNER_ID_CARD | VARCHAR2(100) | Y |  |
| BIRTHDAY | VARCHAR2(30) | Y |  |
| CO_SIGNATORIES_NAME | VARCHAR2(100) | Y |  |
| CO_SIGNATORIES_ID | VARCHAR2(50) | Y |  |

### JAE_CITIC_PS_BASE_INFO

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| STATION_NO | VARCHAR2(50) | Y |  |
| STATION_STATUS | NUMBER(22) | Y |  |
| PROJECT_COMPANY_NAME | VARCHAR2(200) | Y |  |
| PROJECT_CODE | VARCHAR2(32) | Y |  |
| PROVINCE_CODE | VARCHAR2(100) | Y |  |
| CITY_CODE | VARCHAR2(100) | Y |  |
| AREA_CODE | VARCHAR2(100) | Y |  |
| DETAIL_ADDRESS | VARCHAR2(1900) | Y |  |
| RECORD_WAY | NUMBER(22) | Y |  |
| COMPONENT_NUM | NUMBER(38) | Y |  |
| POWER | NUMBER(22) | Y |  |
| CAPACITY | NUMBER(38) | Y |  |
| INVERTER_NUM | NUMBER(22) | Y |  |
| PRODUCT_TYPE | VARCHAR2(255) | Y |  |
| ACCOUNT_TYPE | NUMBER(22) | Y |  |
| ACCOUNT_USER_NAME | VARCHAR2(100) | Y |  |
| ACCOUNT_NUM | VARCHAR2(100) | Y |  |
| OPEN_BANK | VARCHAR2(300) | Y |  |
| STATION_COST | NUMBER(22) | Y |  |
| BUSINESS_STATUS | NUMBER(22) | Y |  |
| GENERATOR_NUMBER | VARCHAR2(200) | Y |  |
| DEDUCTION_ACCOUNT_TYPE | NUMBER(22) | Y |  |
| DEDUCTION_ACCOUNT_NAME | VARCHAR2(255) | Y |  |
| DEDUCTION_ACCOUNT_NUM | VARCHAR2(100) | Y |  |
| DEDUCTION_ACCOUNT_BANK | VARCHAR2(255) | Y |  |
| EFFECTIVE_DATE | VARCHAR2(10) | Y |  |
| GRID_DATE | VARCHAR2(10) | Y |  |

### JAE_CITIC_PS

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| ID | NUMBER(22) | Y |  |
| STATIONNO | VARCHAR2(50) | Y |  |
| PROJECTCOMP | VARCHAR2(255) | Y |  |
| PROVINCE | VARCHAR2(50) | Y |  |
| CITY | VARCHAR2(50) | Y |  |
| BATCHNO | VARCHAR2(50) | Y |  |
| PRODTYPE | VARCHAR2(50) | Y |  |
| CAP | NUMBER(22) | Y |  |
| FEE | NUMBER(22) | Y |  |
| FEE_DATE | DATE(7) | Y |  |
| FEE_STATUS | VARCHAR2(20) | Y |  |
| CITIC_PROJCOMP_CODE | VARCHAR2(32) | Y |  |
| CITIC_PS_NO | VARCHAR2(32) | Y |  |
| STATION_COST | NUMBER(22) | Y |  |
| BUSINESS_STATUS | NUMBER(22) | Y |  |

### JAE_CITIC_PS_SCOPE

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| ID | NUMBER(22) | N |  |
| STATION_NO | VARCHAR2(50) | Y |  |
| PROJ_COMP | VARCHAR2(50) | Y |  |
| PROVINCE | VARCHAR2(50) | Y |  |
| CITY | VARCHAR2(50) | Y |  |
| BATCH | VARCHAR2(50) | Y |  |
| PROD | VARCHAR2(50) | Y |  |
| CAP | NUMBER(22) | Y |  |
| FEE | NUMBER(22) | Y |  |
| FEE_DATE | DATE(7) | Y |  |
| FEE_STATUS | VARCHAR2(50) | Y |  |

### JAE_DAILY_POWER_ABNORMAL

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| STATION_NUMBER | VARCHAR2(256) | Y |  |
| POWER_MONTH | NUMBER(22) | Y |  |
| PRODUCEDAY | NUMBER(8) | Y |  |
| POWER_AMOUNT | BINARY_DOUBLE(8) | Y |  |
| POWER0_DATE_RECORD | NUMBER(8) | Y |  |
| POWER0_DAYS | NUMBER(22) | Y |  |
| LAST_ACTIVE_DATE | NUMBER(22) | Y |  |

### JAE_RENTAL_PRICE_PROVINCE
**注释:** 各省租金

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| ID | NUMBER(22) | N |  |
| PROVINCE | VARCHAR2(240) | Y | 省 |
| CITY | VARCHAR2(240) | Y | 市 |
| AREA | VARCHAR2(240) | Y | 区 |
| INSTALL_SHEME | VARCHAR2(240) | Y | 安装方案 |
| PHASE1_MONS | NUMBER(22) | Y | 一阶段（前年）月数 |
| PHASE1_PRICE | NUMBER(22) | Y | 一阶段（前年）租金 |
| PHASE2_MONS | NUMBER(22) | Y | 二阶段（后年）月数 |
| PHASE2_PRICE | NUMBER(22) | Y | 二阶段（后年）租金 |
| START_TIME | DATE(7) | Y |  |
| END_TIME | DATE(7) | Y |  |

### JAE_OA_COMPANY_ENTITY

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| ID | NUMBER(22) | N |  |
| COMP_NAME | VARCHAR2(255) | Y |  |

### JAE_POWER_PRICE_PROVINCE

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| ID | NUMBER(22) | N |  |
| PROVINCE | VARCHAR2(160) | Y |  |
| PRICE | NUMBER(22) | Y |  |
| UPDATE_DATE | DATE(7) | Y |  |

### JAE_PROVINCE

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| ID | NUMBER(22) | N |  |
| PROVINCE | VARCHAR2(50) | Y |  |
| LATITUDE | NUMBER(22) | Y |  |
| LONGITUDE | NUMBER(22) | Y |  |

### EMP

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| EMPNO | NUMBER(4) | N |  |
| ENAME | VARCHAR2(50) | Y |  |
| JOB | VARCHAR2(50) | Y |  |
| MGR | NUMBER(4) | Y |  |
| HIREDATE | DATE(7) | Y |  |
| SAL | NUMBER(7,2) | Y |  |
| COMM | NUMBER(7,2) | Y |  |
| DEPTNO | NUMBER(4) | Y |  |

### DEPT

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| DEPTNO | NUMBER(4) | N |  |
| DNAME | VARCHAR2(50) | Y |  |
| LOC | VARCHAR2(50) | Y |  |
| CREATE_TIME | DATE(7) | Y |  |
| UPDATE_TIME | DATE(7) | Y |  |

### JAE_RENTAL_PRICE_PROVINCE_ERR$
**注释:** DML Error Logging table for "JAE_RENTAL_PRICE_PROVINCE"

| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| ORA_ERR_NUMBER$ | NUMBER(22) | Y |  |
| ORA_ERR_MESG$ | VARCHAR2(2000) | Y |  |
| ORA_ERR_ROWID$ | UROWID(4000) | Y |  |
| ORA_ERR_OPTYP$ | VARCHAR2(2) | Y |  |
| ORA_ERR_TAG$ | VARCHAR2(2000) | Y |  |
| ID | VARCHAR2(4000) | Y |  |
| PROVINCE | VARCHAR2(4000) | Y |  |
| CITY | VARCHAR2(4000) | Y |  |
| AREA | VARCHAR2(4000) | Y |  |
| INSTALL_SHEME | VARCHAR2(4000) | Y |  |
| PHASE1_MONS | VARCHAR2(4000) | Y |  |
| PHASE1_PRICE | VARCHAR2(4000) | Y |  |
| PHASE2_MONS | VARCHAR2(4000) | Y |  |
| PHASE2_PRICE | VARCHAR2(4000) | Y |  |
| START_TIME | VARCHAR2(4000) | Y |  |
| END_TIME | VARCHAR2(4000) | Y |  |

## 外键关系

| 子表 | 子表字段 | 父表 | 父表字段 |
|------|---------|------|---------|
| EMP | DEPTNO | DEPT | DEPTNO |
| EMP | MGR | EMP | EMPNO |

## 主键

| 表名 | 字段 | 位置 |
|------|------|------|
| BIN$SnBvNuGOixPgYx9kHazklA==$0 | ID | - |
| BIN$TCuCFg1diUTgYx9kHawBXw==$0 | ID | - |
| BIN$TCuCFg1jiUTgYx9kHawBXw==$0 | ID | - |
| BIN$TCuIocAViWTgYx9kHayCYQ==$0 | DEPTNO | - |
| BIN$TCuIocAZiWTgYx9kHayCYQ==$0 | ID | - |
| DEPT | DEPTNO | - |
| EMP | EMPNO | - |
| JAE_CITIC_PS_SCOPE | ID | - |
| JAE_OA_COMPANY_ENTITY | ID | - |
| JAE_POWER_PRICE_PROVINCE | ID | - |
| JAE_PROVINCE | ID | - |
| JAE_RENTAL_PRICE_PROVINCE | ID | - |


<!--
```json
{
  "schema_name": "    ",
  "db_type": "oracle",
  "tables": {
    "JAE_MONTHLY_POWER_FEE": {
      "columns": [
        "STATIONNO",
        "MEDIUMID",
        "STATION_COUNT_PER_CARD",
        "POWERMONTH",
        "POWER_AMOUNT",
        "PRICE",
        "POWER_FEE_THEORETICAL",
        "CARD_POWER_SUM",
        "CARD_TOTAL_RECEIPT",
        "ALLOCATED_FEE",
        "CLOSING_BALANCE",
        "CARD_TOTAL_DEDUCT"
      ],
      "pk": []
    },
    "JAE_PS_BOM": {
      "columns": [
        "DIPATCHTIME_CONFIRM",
        "STATIONNO",
        "INTENTIONSTATE",
        "AGENT",
        "MATERIALCODE",
        "MATERIALNAME",
        "PROPERTYOWNER",
        "ITEMGROUP",
        "EQUIPMENTNUMBER",
        "COLLECTORNUMBER",
        "UNIT",
        "DESIGNQUANTITY",
        "ENGINEERINGQUANTITY",
        "UNITPRICE",
        "POWER",
        "DIPATCHTIME",
        "ENDCHECKTIME"
      ],
      "pk": []
    },
    "JAE_MONTHLY_POWER_COMPARE": {
      "columns": [
        "STATION_NUMBER",
        "CURRENT_MONTH",
        "CURRENT_SUM",
        "RECORD_MONTH",
        "RECORD_AMOUNT",
        "TOTAL_POWER",
        "LAST_ACTIVE_DATE"
      ],
      "pk": []
    },
    "JAE_PS": {
      "columns": [
        "ORDERID",
        "STATIONNO",
        "HOUSEHOLDER_NAME",
        "HOUSEHOLDER_ID",
        "HOUSEHOLDER_PHONE",
        "PROVINCE",
        "CITY",
        "DISTRICT",
        "TOWN",
        "PSADDRESS",
        "LATITUDE",
        "LONGITUDE",
        "COLLECTIONTYPE",
        "PRODUCT_NAME",
        "BUSINESS_TYPE",
        "MERGE_FILING_TYPE",
        "PS_TYPE",
        "PROJECT_COMPANY_NAME",
        "EPC",
        "DEVELOPER_CODE",
        "DEVELOPER_NAME",
        "SERVICE_PROVIDER_CODE",
        "SERVICE_PROVIDER_NAME",
        "AGENT_CODE",
        "AGENT_NAME",
        "AGENT_LECAL",
        "AGENT_PHONE",
        "AGENT_LICENSE",
        "AGENT_ADDR",
        "PS_STATE",
        "POWER_ACCOUNT",
        "FILING_CERT_CODE",
        "COSIGNER_NAME",
        "COSIGNER_ID",
        "COSIGNER_PHONE",
        "RENT_SHARE_BANK_NAME",
        "DESIGN_SCHEME",
        "DESIGN_MODULE_TOTAL_PIECES",
        "DESIGN_TOTAL_CAPACITY",
        "SPEC_SOLUTION_TYPE",
        "SPEC_SOLUTION_PIECES",
        "INVERTER_COUNT",
        "CONTRACT_SIGN_TYPE",
        "FIRSTSTAGE_YEARCOUNT",
        "FIRSTSTAGE_SHAREMONEY",
        "SECONDSTAGE_YEARCOUNT",
        "SECONDSTAGE_SHAREMONEY",
        "THIRDSTAGE_YEARCOUNT",
        "THIRDSTAGE_SHAREMONEY",
        "BUSINESS_CREATE_DATE",
        "SURVEY_FINISH_DATE",
        "CONTRACT_CREATE_DATE",
        "CONTRACT_MERGE_DATE",
        "FILING_SUBMIT_DATE",
        "BUSINESS_REVIEW_FINISH_DATE",
        "TECH_REVIEW_FINISH_DATE",
        "FILING_REVIEW_PASSED_DATE",
        "FULL_DELIVER_DATE",
        "DIPATCH_DATE",
        "COMPLETE_SUBMIT_DATE",
        "COMPLETE_CHECK_DATE",
        "MERGE_APPLY_DATE",
        "MERGE_BUSSINESS_REVIEW_DATE",
        "MERGE_ENGINEERING_REVIEW_DATE",
        "MERGE_REVIEW_PASS_DATE",
        "COMPLETE_DATE",
        "FIRST_POWER_DATE",
        "CONTRACT_SIGN_DATE",
        "BUSINESS_OPPT_NO",
        "BUSINESS_OPPT_STATUS",
        "RENT_SHARE_BANK_ACCOUNT_NAME",
        "RENT_SHARE_BANK_ACCOUNT_NUM",
        "RENT_SHARE_BANK_CODE",
        "GRID_EARNING_BANK_ACCOUNT_NUM",
        "GRID_EARNING_BANK_NAME",
        "GRID_EARNING_BANK_ACCOUNT_NAME",
        "DEDUCTION_BANK_ACCOUNT_NAME",
        "DEDUCTION_BANK_ACCOUNT_NUM",
        "DEDUCTION_BANK_NAME",
        "MODULE_TOTAL_PIECES",
        "MODULE_POWER",
        "TOTAL_CAPACITY",
        "CONTRACT_SIGN_STATUS",
        "CONTRACT_SIGN_SECONDPART",
        "CONTRACT_FIRST_EFFECTIVE_DATE",
        "BIRTHDAY",
        "OWNWER_SIGN_AGE",
        "PROVINCE_CODE",
        "CITY_CODE",
        "DISTRICT_CODE",
        "TOWN_CODE",
        "PROJCOMP_BANK_ACCOUNT",
        "PROJCOMP_BANK_NAME",
        "INCOME_START_DATE",
        "TAG_STATUS"
      ],
      "pk": []
    },
    "JAE_CITIC_OWNER_INFO": {
      "columns": [
        "STATION_NO",
        "OWNER_NAME",
        "OWNER_ID_CARD",
        "BIRTHDAY",
        "CO_SIGNATORIES_NAME",
        "CO_SIGNATORIES_ID"
      ],
      "pk": []
    },
    "JAE_CITIC_PS_BASE_INFO": {
      "columns": [
        "STATION_NO",
        "STATION_STATUS",
        "PROJECT_COMPANY_NAME",
        "PROJECT_CODE",
        "PROVINCE_CODE",
        "CITY_CODE",
        "AREA_CODE",
        "DETAIL_ADDRESS",
        "RECORD_WAY",
        "COMPONENT_NUM",
        "POWER",
        "CAPACITY",
        "INVERTER_NUM",
        "PRODUCT_TYPE",
        "ACCOUNT_TYPE",
        "ACCOUNT_USER_NAME",
        "ACCOUNT_NUM",
        "OPEN_BANK",
        "STATION_COST",
        "BUSINESS_STATUS",
        "GENERATOR_NUMBER",
        "DEDUCTION_ACCOUNT_TYPE",
        "DEDUCTION_ACCOUNT_NAME",
        "DEDUCTION_ACCOUNT_NUM",
        "DEDUCTION_ACCOUNT_BANK",
        "EFFECTIVE_DATE",
        "GRID_DATE"
      ],
      "pk": []
    },
    "JAE_CITIC_PS": {
      "columns": [
        "ID",
        "STATIONNO",
        "PROJECTCOMP",
        "PROVINCE",
        "CITY",
        "BATCHNO",
        "PRODTYPE",
        "CAP",
        "FEE",
        "FEE_DATE",
        "FEE_STATUS",
        "CITIC_PROJCOMP_CODE",
        "CITIC_PS_NO",
        "STATION_COST",
        "BUSINESS_STATUS"
      ],
      "pk": []
    },
    "JAE_CITIC_PS_SCOPE": {
      "columns": [
        "ID",
        "STATION_NO",
        "PROJ_COMP",
        "PROVINCE",
        "CITY",
        "BATCH",
        "PROD",
        "CAP",
        "FEE",
        "FEE_DATE",
        "FEE_STATUS"
      ],
      "pk": [
        "ID"
      ]
    },
    "JAE_DAILY_POWER_ABNORMAL": {
      "columns": [
        "STATION_NUMBER",
        "POWER_MONTH",
        "PRODUCEDAY",
        "POWER_AMOUNT",
        "POWER0_DATE_RECORD",
        "POWER0_DAYS",
        "LAST_ACTIVE_DATE"
      ],
      "pk": []
    },
    "JAE_RENTAL_PRICE_PROVINCE": {
      "columns": [
        "ID",
        "PROVINCE",
        "CITY",
        "AREA",
        "INSTALL_SHEME",
        "PHASE1_MONS",
        "PHASE1_PRICE",
        "PHASE2_MONS",
        "PHASE2_PRICE",
        "START_TIME",
        "END_TIME"
      ],
      "pk": [
        "ID"
      ]
    },
    "JAE_OA_COMPANY_ENTITY": {
      "columns": [
        "ID",
        "COMP_NAME"
      ],
      "pk": [
        "ID"
      ]
    },
    "JAE_POWER_PRICE_PROVINCE": {
      "columns": [
        "ID",
        "PROVINCE",
        "PRICE",
        "UPDATE_DATE"
      ],
      "pk": [
        "ID"
      ]
    },
    "JAE_PROVINCE": {
      "columns": [
        "ID",
        "PROVINCE",
        "LATITUDE",
        "LONGITUDE"
      ],
      "pk": [
        "ID"
      ]
    },
    "EMP": {
      "columns": [
        "EMPNO",
        "ENAME",
        "JOB",
        "MGR",
        "HIREDATE",
        "SAL",
        "COMM",
        "DEPTNO"
      ],
      "pk": [
        "EMPNO"
      ]
    },
    "DEPT": {
      "columns": [
        "DEPTNO",
        "DNAME",
        "LOC",
        "CREATE_TIME",
        "UPDATE_TIME"
      ],
      "pk": [
        "DEPTNO"
      ]
    },
    "JAE_RENTAL_PRICE_PROVINCE_ERR$": {
      "columns": [
        "ORA_ERR_NUMBER$",
        "ORA_ERR_MESG$",
        "ORA_ERR_ROWID$",
        "ORA_ERR_OPTYP$",
        "ORA_ERR_TAG$",
        "ID",
        "PROVINCE",
        "CITY",
        "AREA",
        "INSTALL_SHEME",
        "PHASE1_MONS",
        "PHASE1_PRICE",
        "PHASE2_MONS",
        "PHASE2_PRICE",
        "START_TIME",
        "END_TIME"
      ],
      "pk": []
    }
  },
  "fk_graph": {
    "EMP": {
      "DEPTNO": {
        "parent_table": "DEPT",
        "parent_column": "DEPTNO"
      },
      "MGR": {
        "parent_table": "EMP",
        "parent_column": "EMPNO"
      }
    }
  },
  "discovered_at": "2026-04-30 09:42:47"
}
```
-->