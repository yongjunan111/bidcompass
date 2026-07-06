조달청 공공데이터 개방

OpenAPI 참고자료

[1. 서비스 명세    3](#_Toc460578917)

[1.1 나라장터 낙찰정보서비스    3](#_Toc460578918)

[가. 서비스 개요    3](#_Toc460578919)

[나. 오퍼레이션 목록    4](#_Toc460578920)

**<br>**

**개정 이력**

| 버 전 | 변경일 | 변경 구분 | 변경사유 |
| --- | --- | --- | --- |
| 1.0 | 2025 | 최초 개정 | 최초 개정 |
| 1.1 | 2025.09.25 | 항목추가 | -요청메시지 사업자번호(bizno) 공공데이터 제공신청으로 인한 추가<br>-대상오퍼레이션<br>- 나라장터 검색조건에 의한 낙찰된 목록 현황 물품조회<br>- 나라장터 검색조건에 의한 낙찰된 목록 현황 공사조회<br>- 나라장터 검색조건에 의한 낙찰된 목록 현황 용역조회<br>- 나라장터 검색조건에 의한 낙찰된 목록 현황 외자조회<br>-응답메시지 입찰가격점수(bidPrceEvlVal), 기술평가점수(techEvlVal),기술평가원점수(techEvlNaturVal) 종합평가점수(totalEvlAmtVal) 공공데이터 제공신청으로 인한 추가<br>-대상오퍼레이션<br>- 개찰결과 개찰완료 목록 조회 |
|   |   |   |   |
|   |   |   |   |
|   |   |   |   |
|   |   |   |   |

<br>

# 1. 서비스 명세

## 1.1 나라장터 낙찰정보서비스

### 서비스 개요

| 서비스 정보 | 서비스 ID |   | **ScsbidInfoService** |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   | 서비스명(국문) |   | 나라장터 낙찰정보서비스 |   |   |   |   |   |
|   | 서비스명(영문) |   | **ScsbidInfoService** |   |   |   |   |   |
|   | 서비스 설명 |   | 나라장터 개찰결과를 물품, 공사, 용역, 외자의 업무별로 제공하는 서비스로 각 업무별로 최종낙찰자, 개찰순위, 복수예비가 및 예비가격 정보를 제공하며 개찰완료목록, 재입찰목록, 유찰목록 또한 제공하는 나라장터 낙찰정보서비스 |   |   |   |   |   |
| 서비스 보안 | 서비스 인증/권한 |   | [O] 서비스 Key[ ] 인증서 (GPKI)<br>[] Basic (ID/PW) [ ] 없음 |   |   |   |   | [ ]WS-Security |
|   | 메시지 레벨 암호화 |   | [  ] 전자서명    [ ] 암호화    [O] 없음 |   |   |   |   |   |
|   | 전송 레벨 암호화 |   | [  ] SSL            [ O] 없음 |   |   |   |   |   |
| 적용 기술 수준 | 인터페이스 표준 |   | [  ] SOAP 1.2<br>(RPC-Encoded, Document Literal, Document Literal Wrapped)<br>[ O ] REST (GET)<br>[ ] RSS 1.0 [ ] RSS 2.0 [ ] Atom 1.0 [ ] 기타 |   |   |   |   |   |
|   | 교환 데이터 표준 |   | [ O ] XML    [ O ] JSON    [ ] MIME    [ ] MTOM |   |   |   |   |   |
| 서비스 URL | 개발환경 |   | http://apis.data.go.kr/1230000/as/**ScsbidInfoService** |   |   |   |   |   |
|   | 운영환경 |   | http://apis.data.go.kr/1230000/as/**ScsbidInfoService** |   |   |   |   |   |
| 서비스 WADL | 개발환경 |   | N/A |   |   |   |   |   |
|   | 운영환경 |   | N/A |   |   |   |   |   |
| 서비스 배포 정보 | 서비스 버전 |   | 1.5 |   |   |   |   |   |
|   | 서비스 시작일 |   | 2025-01-06 |   | 배포 일자 |   | 2025-01-06 |   |
|   | 서비스 이력 |   | N/A |   |   |   |   |   |
| 메시지 교환 유형 | [O] Request-Response    [ ] Publish-Subscribe<br>[ ] Fire-and-Forgot        [ ] Notification |   |   |   |   |   |   |   |
| 메시지 로깅 수준 | 성공 | [O] Header [ ] Body |   | 실패 |   | [O] Header [O} Body |   |   |
| 사용 제약 사항 (비고) | N/A |   |   |   |   |   |   |   |
| 서비스 제공자 | 차도빈 / 조달청 전자조달기획과 / 042-724-7124 / dobin@korea.kr |   |   |   |   |   |   |   |
| 데이터 갱신주기 | 수시 |   |   |   |   |   |   |   |

### 오퍼레이션 목록

| 일련번호 | 서비스명(국문) | 오퍼레이션명(영문) | 오퍼레이션명(국문) | 메시지명(영문) |
| --- | --- | --- | --- | --- |
| 1 | 나라장터 낙찰정보서비스 | **getScsbidListSttusThng** | 낙찰된 목록 현황 물품조회 | N/A |
| 2 |   | **getScsbidListSttusCnstwk** | 낙찰된 목록 현황 공사조회 | N/A |
| 3 |   | **getScsbidListSttusServc** | 낙찰된 목록 현황 용역조회 | N/A |
| 4 |   | **getScsbidListSttusFrgcpt** | 낙찰된 목록 현황 외자조회 | N/A |

| 일련번호 | 서비스명(국문) | 오퍼레이션명(영문) | 오퍼레이션명(국문) | 메시지명(영문) |
| --- | --- | --- | --- | --- |
| 5 | 나라장터 낙찰정보서비스 | **getOpengResultListInfoThng** | 개찰결과 물품 목록 조회 | N/A |
| 6 |   | **getOpengResultListInfoCnstwk** | 개찰결과 공사 목록 조회 | N/A |
| 7 |   | **getOpengResultListInfoServc** | 개찰결과 용역 목록 조회 | N/A |
| 8 |   | **getOpengResultListInfoFrgcpt** | 개찰결과 외자 목록 조회 | N/A |
| 9 |   | **getOpengResultListInfoThngPreparPcDetail** | 개찰결과 물품 예비가격상세 목록 조회 | N/A |
| 10 |   | **getOpengResultListInfoCnstwkPreparPcDetail** | 개찰결과 공사 예비가격상세 목록 조회 | N/A |
| 11 |   | **getOpengResultListInfoServcPreparPcDetail** | 개찰결과 용역 예비가격상세 목록 조회 | N/A |
| 12 |   | **getOpengResultListInfoFrgcptPreparPcDetail** | 개찰결과 외자 예비가격상세 목록 조회 | N/A |
| 13 |   | **getOpengResultListInfoOpengCompt** | 개찰결과 개찰완료 목록 조회 | N/A |
| 14 |   | **getOpengResultListInfoFailing** | 개찰결과 유찰 목록 조회 | N/A |
| 15 |   | **getOpengResultListInfoRebid** | 개찰결과 재입찰 목록 조회 | N/A |
| 16. |   | **getScsbidListSttusThngPPSSrch** | 나라장터 검색조건에 의한 낙찰된 목록 현황 물품조회 | N/A |
| 17 |   | **getScsbidListSttusCnstwkPPSSrch** | 나라장터 검색조건에 의한 낙찰된 목록 현황 공사조회 | N/A |
| 18 |   | **getScsbidListSttusServcPPSSrch** | 나라장터 검색조건에 의한 낙찰된 목록 현황 용역조회 | N/A |
| 19 |   | **getScsbidListSttusFrgcptPPSSrch** | 나라장터 검색조건에 의한 낙찰된 목록 현황 외자조회 | N/A |
| 20 |   | **getOpengResultListInfoThngPPSSrch** | 나라장터 검색조건에 의한 개찰결과 물품 목록 조회 | N/A |
| 21 |   | **getOpengResultListInfoCnstwkPPSSrch** | 나라장터 검색조건에 의한 개찰결과 공사 목록 조회 | N/A |
| 22 |   | **getOpengResultListInfoServcPPSSrch** | 나라장터 검색조건에 의한 개찰결과 용역 목록 조회 | N/A |
| 23 |   | **getOpengResultListInfoFrgcptPPSSrch** | 나라장터 검색조건에 의한 개찰결과 외자 목록 조회 | N/A |

#### <br>[낙찰된 목록 현황 물품조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 1 | 오퍼레이션명(국문) | 낙찰된 목록 현황 물품조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | getScsbidListSttusThng |   |
|   | 오퍼레이션 설명 | 검색조건을 등록일시, 공고일시, 개찰일시, 입찰공고번호로 물품에 대한 나라장터 최종낙찰자 목록(입찰공고번호, 입찰공고명, 참가업체수, 최종낙찰업체명, 사업자번호, 최종낙찰률, 실개찰일시, 수요기관, 최종낙찰일, 최종낙찰업체담당자)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

                1. 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |   |
| --- | --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |   |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |   |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |   |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |   |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.등록일시, 2.공고일시,3.개찰일시, 4.입찰공고번호 |   |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |   |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |   |
| bidNtceNo | 입찰공고번호 | 40 | 0 | R25BK00965123 | 검색하고자하는 입찰공고번호<br>조회구분 4인 경우 필수 |   |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 수 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 40 | 1 | R25BK00965123 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| ntceDivCd | 공고구분코드 | 7 | 1 | 통050001 | 공고구분<br>통050001 : 조달청 또는 나라장터 자체 공고건 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 혁신육아복합센터 건립공사(기계) 관급자재(간접가열보일러) | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| prtcptCnum | 참가업체수 | 6 | 0 | 2 | 참가업체수 |
| bidwinnrNm | 최종낙찰업체명 | 200 | 1 | 주식회사 동광보일러 | 최종낙찰된 업체의 명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrBizno | **최종낙찰업체사업자등록번호** | 10 | 1 | 1408121883 | 협상이 완료 후 최종낙찰된 업체의 사업자등록번호임 |
| bidwinnrCeoNm | 최종낙찰업체대표자명 | 35 | 0 | 박정연 | 최종낙찰된 업체의 대표자명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrAdrs | 최종낙찰업체주소 | 200 | 0 | 충청남도 아산시 수장로 67-0 (배미동) | 협상이 완료 후 최종낙찰된 업체의 주소임 |
| bidwinnrTelNo | 최종낙찰업체전화번호 | 25 | 0 | 02-6258-8989 | 협상이 완료 후 최종낙찰된 업체의 연락 전화번호임<br>핸드폰번호는 “*”로 표기 |
| sucsfbidAmt | 최종낙찰금액 | 21 | 0 | 83500000 | 최종낙찰은 개찰순위 순서대로 협상등을 통해 최종 낙찰된정보를 의미하며 최종낙찰금액은 최종낙찰된 금액 (원화,원)으로 개찰완료된건에 대하여 제공 |
| sucsfbidRate | **최종낙찰률** | 18 | 0 | 97.82 | 예정가격대비 최종낙찰금액으로 최종낙찰금액/예정가격 * 100 으로 계산되며 개찰완료된 건에 대하여 제공 (%) |
| rlOpengDt | **실개찰일시** | 19 | 0 | 2025-07-23 11:00:00 | 실제 개찰일시  “YYYY-MM-DD HH:MM:SS” |
| dminsttCd | 수요기관코드 | 7 | 0 | 6280147 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 인천광역시 종합건설본부 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| rgstDt | 등록일시 | 19 | 1 | 2025-07-23 15:20:05 | 등록일시 "YYYY-MM-DD HH:MM:SS" |
| fnlSucsfDate | 최종낙찰일자 | 10 | 0 | 2025-07-23 | 최종낙찰된 일자로 개찰완료된 건에 대하여 제공 |
| fnlSucsfCorpOfcl | 최종낙찰업체담당자 | 35 | 0 | N/A | 최종낙찰된 업체의 담당자명으로 개찰완료된 건에 대하여 제공 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getScsbidListSttusThng?inqryDiv=4&bidNtceNo =R25BK00965123&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00965123</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><ntceDivCd>통050001</ntceDivCd><br><bidNtceNm>혁신육아복합센터 건립공사(기계) 관급자재(간접가열보일러)</bidNtceNm><br><prtcptCnum>2</prtcptCnum><br><bidwinnrNm>주식회사 동광보일러</bidwinnrNm><br><bidwinnrBizno>1408121883</bidwinnrBizno><br><bidwinnrCeoNm>박정연</bidwinnrCeoNm><br><bidwinnrAdrs>충청남도 아산시 수장로 67-0 (배미동)</bidwinnrAdrs><br><bidwinnrTelNo>02-6258-8989</bidwinnrTelNo><br><sucsfbidAmt>83500000</sucsfbidAmt><br><sucsfbidRate>97.82</sucsfbidRate><br><rlOpengDt>2025-07-23 11:00:00</rlOpengDt><br><dminsttCd>6280147</dminsttCd><br><dminsttNm>인천광역시 종합건설본부</dminsttNm><br><rgstDt>2025-07-23 15:20:05</rgstDt><br><fnlSucsfDate>2025-07-23</fnlSucsfDate><br><fnlSucsfCorpOfcl></fnlSucsfCorpOfcl><br></item><br></items><br><numOfRows>999</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

#### [낙찰된 목록 현황 공사조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 2 | 오퍼레이션명(국문) | 낙찰된 목록 현황 공사조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getScsbidListSttusCnstwk** |   |
|   | 오퍼레이션 설명 | 검색조건을 등록일시, 공고일시, 개찰일시, 입찰공고번호로 공사에대한 나라장터 최종낙찰자 목록(입찰공고번호, 입찰공고명, 참가업체수, 최종낙찰업체명, 사업자번호, 최종낙찰률, 실개찰일시, 수요기관, 최종낙찰일, 최종낙찰업체담당자)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.등록일시, 2.공고일시,3.개찰일시,4.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 40 | 0 | R25BK00922727 | 검색하고자하는 입찰공고번호<br>조회구분 4인 경우 필수 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 수 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 40 | 1 | R25BK00922727 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 0 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| ntceDivCd | 공고구분코드 | 7 | 1 | 통050001 | 공고구분<br>통050001 : 조달청 또는 나라장터 자체 공고건 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | (입찰대행)신활력플러스 군지정형 어르신영농단 지원사업 | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| prtcptCnum | 참가업체수 | 6 | 0 | 15 | 참가업체수 |
| bidwinnrNm | 최종낙찰업체명 | 200 | 1 | 유한회사대가건설 | 최종낙찰된 업체의 명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrBizno | 최종낙찰업체사업자등록번호 | 10 | 1 | 4188124255 | 협상이 완료 후 최종낙찰된 업체의 사업자등록번호임 |
| bidwinnrCeoNm | 최종낙찰업체대표자명 | 35 | 0 | 강훈희 | 최종낙찰된 업체의 대표자명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrAdrs | 최종낙찰업체주소 | 200 | 0 | 전북특별자치도 부안군 부안읍 서외리 455-3,제1층 제3호 | 협상이 완료 후 최종낙찰된 업체의 주소임 |
| bidwinnrTelNo | 최종낙찰업체전화번호 | 25 | 0 | 063-581-8121 | 협상이 완료 후 최종낙찰된 업체의 연락 전화번호임<br>핸드폰번호는 “*”로 표기 |
| sucsfbidAmt | 최종낙찰금액 | 21 | 0 | 58708988 | 최종낙찰은 개찰순위 순서대로 협상등을 통해 최종 낙찰된정보를 의미하며 최종낙찰금액은 최종낙찰된 금액 (원화,원)으로 개찰완료된건에 대하여 제공 |
| sucsfbidRate | 최종낙찰률 | 18 | 0 | 90.278 | 예정가격대비 최종낙찰금액으로 최종낙찰금액/예정가격 * 100 으로 계산되며 개찰완료된 건에 대하여 제공 (%) |
| rlOpengDt | 실개찰일시 | 19 | 0 | 2025-06-27 12:00:00 | 실제 개찰일시  “YYYY-MM-DD HH:MM:SS” |
| dminsttCd | 수요기관코드 | 7 | 0 | 4791000 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 전북특별자치도 부안군 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| rgstDt | 등록일시 | 19 | 1 | 2025-07-01 13:54:43 | 등록일시 "YYYY-MM-DD HH:MM:SS" |
| fnlSucsfDate | 최종낙찰일자 | 10 | 0 | 2025-07-01 | **최종낙찰된 일자로 개찰완료된 건에 대하여 제공** |
| fnlSucsfCorpOfcl | 최종낙찰업체담당자 | 35 | 0 | N/A | **최종낙찰된 업체의 담당자명으로 개찰완료된 건에 대하여 제공** |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getScsbidListSttusCnstwk?inqryDiv=4& bidNtceNo= R25BK00922727&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00922727</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><ntceDivCd>통050001</ntceDivCd><br><bidNtceNm>(입찰대행)신활력플러스 군지정형 어르신영농단 지원사업</bidNtceNm><br><prtcptCnum>15</prtcptCnum><br><bidwinnrNm>유한회사대가건설</bidwinnrNm><br><bidwinnrBizno>4188124255</bidwinnrBizno><br><bidwinnrCeoNm>강훈희</bidwinnrCeoNm><br><bidwinnrAdrs>전북특별자치도 부안군 부안읍 서외리 455-3,제1층 제3호</bidwinnrAdrs><br><bidwinnrTelNo>063-581-8121</bidwinnrTelNo><br><sucsfbidAmt>58708988</sucsfbidAmt><br><sucsfbidRate>90.278</sucsfbidRate><br><rlOpengDt>2025-06-27 12:00:00</rlOpengDt><br><dminsttCd>4791000</dminsttCd><br><dminsttNm>전북특별자치도 부안군</dminsttNm><br><rgstDt>2025-07-01 13:54:43</rgstDt><br><fnlSucsfDate>2025-07-01</fnlSucsfDate><br><fnlSucsfCorpOfcl></fnlSucsfCorpOfcl><br></item><br></items><br><numOfRows>999</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

#### [낙찰된 목록 현황 용역조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 3 | 오퍼레이션명(국문) | 낙찰된 목록 현황 용역조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getScsbidListSttusServc** |   |
|   | 오퍼레이션 설명 | 검색조건을 등록일시, 공고일시, 개찰일시, 입찰공고번호로 용역에 대한 나라장터 최종낙찰자 목록(입찰공고번호, 입찰공고명, 참가업체수, 최종낙찰업체명, 사업자번호, 최종낙찰률, 실개찰일시, 수요기관, 최종낙찰일, 최종낙찰업체담당자)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.등록일시, 2.공고일시, 3.개찰일시, 4.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 40 | 0 | R25BK00927163 | 검색하고자하는 입찰공고번호<br>조회구분 4인 경우 필수 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 수 |
| totalCount | 데이터 총 개수 | 4 | 1 | 10 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 40 | 1 | R25BK00927163 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 0 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| ntceDivCd | 공고구분코드 | 7 | 1 | 통050001 | 공고구분<br>통050001 : 조달청 또는 나라장터 자체 공고건 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 동물원(해양관, 남미관) 종합안내판 변경 제작 시행 | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| prtcptCnum | 참가업체수 | 6 | 0 | 1 | 참가업체수 |
| bidwinnrNm | 최종낙찰업체명 | 200 | 1 | 주식회사 나무조각 에코사인 | 최종낙찰된 업체의 명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrBizno | 최종낙찰업체사업자등록번호 | 10 | 1 | 1238640842 | 협상이 완료 후 최종낙찰된 업체의 사업자등록번호임 |
| bidwinnrCeoNm | 최종낙찰업체대표자명 | 35 | 0 | 조선미 | 최종낙찰된 업체의 대표자명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrAdrs | 최종낙찰업체주소 | 200 | 0 | 경기도 화성시 기안말길 17-0 (기안동) | 협상이 완료 후 최종낙찰된 업체의 주소임 |
| bidwinnrTelNo | 최종낙찰업체전화번호 | 25 | 0 | 070-8273-0625 | 협상이 완료 후 최종낙찰된 업체의 연락 전화번호임<br>핸드폰번호는 “*”로 표기 |
| sucsfbidAmt | 최종낙찰금액 | 21 | 0 | 38832000 | 최종낙찰은 개찰순위 순서대로 협상등을 통해 최종 낙찰된정보를 의미하며 최종낙찰금액은 최종낙찰된 금액 (원화,원)으로 개찰완료된건에 대하여 제공 |
| sucsfbidRate | 최종낙찰률 | 18 | 0 | 94.999 | 예정가격대비 최종낙찰금액으로 최종낙찰금액/예정가격 * 100 으로 계산되며 개찰완료된 건에 대하여 제공 (%) |
| rlOpengDt | 실개찰일시 | 19 | 0 | 2025-06-30 18:00:00 | 실제 개찰일시  “YYYY-MM-DD HH:MM:SS” |
| dminsttCd | 수요기관코드 | 7 | 0 | 6112581 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 서울특별시 서울대공원 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| rgstDt | 등록일시 | 19 | 1 | 2025-07-01 13:39:16 | 등록일시 "YYYY-MM-DD HH:MM:SS" |
| fnlSucsfDate | 최종낙찰일자 | 10 | 0 | 2025-07-01 | **최종낙찰된 일자로 개찰완료된 건에 대하여 제공** |
| fnlSucsfCorpOfcl | 최종낙찰업체담당자 | 35 | 0 | N/A | **최종낙찰된 업체의 담당자명으로 개찰완료된 건에 대하여 제공** |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getScsbidListSttusServc?inqryDiv=4& bidNtceNo=R25BK00927163&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00927163</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><ntceDivCd>통050001</ntceDivCd><br><bidNtceNm>동물원(해양관, 남미관) 종합안내판 변경 제작 시행</bidNtceNm><br><prtcptCnum>1</prtcptCnum><br><bidwinnrNm>주식회사 나무조각 에코사인</bidwinnrNm><br><bidwinnrBizno>1238640842</bidwinnrBizno><br><bidwinnrCeoNm>조선미</bidwinnrCeoNm><br><bidwinnrAdrs>경기도 화성시 기안말길 17-0 (기안동)</bidwinnrAdrs><br><bidwinnrTelNo>070-8273-0625</bidwinnrTelNo><br><sucsfbidAmt>38832000</sucsfbidAmt><br><sucsfbidRate>94.999</sucsfbidRate><br><rlOpengDt>2025-06-30 18:00:00</rlOpengDt><br><dminsttCd>6112581</dminsttCd><br><dminsttNm>서울특별시 서울대공원</dminsttNm><br><rgstDt>2025-07-01 13:39:16</rgstDt><br><fnlSucsfDate>2025-07-01</fnlSucsfDate><br><fnlSucsfCorpOfcl></fnlSucsfCorpOfcl><br></item><br></items><br><numOfRows>10</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

#### [낙찰된 목록 현황 외자조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 4 | 오퍼레이션명(국문) | 낙찰된 목록 현황 외자조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getScsbidListSttusFrgcpt** |   |
|   | 오퍼레이션 설명 | 검색조건을 등록일시, 공고일시, 개찰일시, 입찰공고번호로 외자에 대한 나라장터 최종낙찰자 목록(입찰공고번호, 입찰공고명, 참가업체수, 최종낙찰업체명, 사업자번호, 최종낙찰률, 실개찰일시, 수요기관, 최종낙찰일, 최종낙찰업체담당자)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.등록일시, 2.공고일시,3.개찰일시,4.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507102359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 40 | 0 | R25BK00857114 | 검색하고자하는 입찰공고번호<br>조회구분 4인 경우 필수 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 수 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 40 | 1 | R25BK00857114 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| ntceDivCd | 공고구분코드 | 7 | 1 | 통050001 | 공고구분<br>통050001 : 조달청 또는 나라장터 자체 공고건 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | (외자)가스크로마토그래프-질량분석기 | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| prtcptCnum | 참가업체수 | 6 | 0 | 1 | 참가업체수 |
| bidwinnrNm | 최종낙찰업체명 | 200 | 1 | 주식회사 시마즈 사이언티픽 코리아 | 최종낙찰된 업체의 명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrBizno | 최종낙찰업체사업자등록번호 | 10 | 1 | 3078701124 | 협상이 완료 후 최종낙찰된 업체의 사업자등록번호임 |
| bidwinnrCeoNm | 최종낙찰업체대표자명 | 35 | 0 | 야마다 타케시 | 최종낙찰된 업체의 대표자명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrAdrs | 최종낙찰업체주소 | 200 | 0 | 서울특별시 강남구 언주로 609, 9층(논현동 , 팍스타워) | 협상이 완료 후 최종낙찰된 업체의 주소임 |
| bidwinnrTelNo | 최종낙찰업체전화번호 | 25 | 0 | 042-864-1161 | 협상이 완료 후 최종낙찰된 업체의 연락 전화번호임<br>핸드폰번호는 “*”로 표기 |
| sucsfbidAmt | 최종낙찰금액 | 21 | 0 | 27538049 | 최종낙찰은 개찰순위 순서대로 협상등을 통해 최종 낙찰된정보를 의미하며 최종낙찰금액은 최종낙찰된 금액 (원화,원)으로 개찰완료된건에 대하여 제공 |
| sucsfbidRate | 최종낙찰률 | 18 | 0 | 0 | 예정가격대비 최종낙찰금액으로 최종낙찰금액/예정가격 * 100 으로 계산되며 개찰완료된 건에 대하여 제공 (%) |
| rlOpengDt | 실개찰일시 | 19 | 0 | 2025-06-05 15:00:00 | 실제 개찰일시  “YYYY-MM-DD HH:MM:SS” |
| dminsttCd | 수요기관코드 | 7 | 0 | 1482021 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 환경부 국립환경과학원 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| rgstDt | 등록일시 | 19 | 1 | 2025-07-07 09:17:48 | 등록일시 "YYYY-MM-DD HH:MM:SS" |
| FnlSucsfDate | 최종낙찰일자 | 10 | 0 | 2025-07-07 | **최종낙찰된 일자로 개찰완료된 건에 대하여 제공** |
| fnlSucsfCorpOfcl | 최종낙찰업체담당자 | 35 | 0 | N/A | **최종낙찰된 업체의 담당자명으로 개찰완료된 건에 대하여 제공** |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getScsbidListSttusFrgcpt?inqryDiv=4& bidNtceNo= R25BK00857114&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00857114</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><ntceDivCd>통050001</ntceDivCd><br><bidNtceNm>(외자)가스크로마토그래프-질량분석기</bidNtceNm><br><prtcptCnum>1</prtcptCnum><br><bidwinnrNm>주식회사 시마즈 사이언티픽 코리아</bidwinnrNm><br><bidwinnrBizno>3078701124</bidwinnrBizno><br><bidwinnrCeoNm>야마다 타케시</bidwinnrCeoNm><br><bidwinnrAdrs>서울특별시 강남구 언주로 609, 9층(논현동 , 팍스타워)</bidwinnrAdrs><br><bidwinnrTelNo>042-864-1161</bidwinnrTelNo><br><sucsfbidAmt>27538049</sucsfbidAmt><br><sucsfbidRate></sucsfbidRate><br><rlOpengDt>2025-06-05 15:00:00</rlOpengDt><br><dminsttCd>1482021</dminsttCd><br><dminsttNm>환경부 국립환경과학원</dminsttNm><br><rgstDt>2025-07-07 09:17:48</rgstDt><br><fnlSucsfDate>2025-07-07</fnlSucsfDate><br><fnlSucsfCorpOfcl></fnlSucsfCorpOfcl><br></item><br></items><br><numOfRows>999</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

#### [개찰결과 물품 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 5 | 오퍼레이션명(국문) | 개찰결과 물품 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoThng** |   |
|   | 오퍼레이션 설명 | 유찰, 개찰완료, 재입찰건에 대한 개찰결과를 제공하며 검색조건을 입력일시, 공고일시, 개찰일시, 입찰공고번호로하여 물품에 대한 나라장터 개찰결과 목록(입찰공고번호, 입찰공고명, 개찰일시, 참가업체수, 개찰업체정보, 진행구분코드명, 입력일시, 예비가격파일존재여부, 공고기관명, 수요기관명)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.입력일시, 2.공고일시, 3.개찰일시, 4.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 11 | 0 | R25BK00840922 | 검색하고자하는 입찰공고번호<br>조회구분 4인 경우 필수 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00840922 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 근접전자기장 내성 시험 시스템 구축 | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| opengDt | 개찰일시 | 19 | 1 | 2025-06-17 11:00:00 | 조달업체가 제출한 입찰서를 개찰하는 일시  “YYYY-MM-DD HH:MM:SS” |
| prtcptCnum | 참가업체수 | 6 | 0 | 2 | 참가업체수 |
| opengCorpInfo | 개찰업체정보 | 500 | 1 | 이엠테스트코리아 주식회사^1428139282^김종인^178750000^97.992 | 개찰업체정보<br>다수 낙찰자의 경우 ”낙찰예정자 다수”와 개찰순위 1위의 투찰금액과 투찰율<br>을 보여줌<br>단일 낙찰자 의 경우 업체명과 사업자번호, 대표자명, 투찰금액, 투찰율을 보여줌<br>단, 협상에 의한 계약일 경우는 투찰금액,투찰율 안나옴 |
| progrsDivCdNm | 진행구분코드명 | 4 | 1 | 개찰완료 | 진행구분이<br>유찰, 개찰완료, 재입찰로 구분 됨 |
| inptDt | 입력일시 | 19 | 0 | 2025-07-14 09:57:49 | 입력일시 “YYYY-MM-DD HH:MM:SS” |
| rsrvtnPrceFileExistnceYn | 예비가격파일존재여부 | 1 | 1 | Y | 예비가격파일존재여부(Y/N) |
| ntceInsttCd | 공고기관코드 | 7 | 1 | 1230137 | 공고를 하는 기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 조달청 대구지방조달청 | 수요기관의 의뢰를 받아 공고하는 기관의 명 |
| dminsttCd | 수요기관코드 | 7 | 0 | Z021943 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 대구경북첨단의료산업진흥재단 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| opengRsltNtcCntnts | 개찰결과공지내용 | 4000 | 0 | 공지내용참고 | 입찰공고번호, 입찰공고차수, 입찰분류번호, 재입찰번호 에 해당하는 공지사항 내용 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoThng?inqryDiv=4& bidNtceNo=R25BK00840922&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00840922</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>근접전자기장 내성 시험 시스템 구축</bidNtceNm><br><opengDt>2025-06-17 11:00:00</opengDt><br><prtcptCnum>2</prtcptCnum><br><opengCorpInfo>이엠테스트코리아 주식회사^1428139282^김종인^178750000^97.992</opengCorpInfo><br><progrsDivCdNm>개찰완료</progrsDivCdNm><br><inptDt>2025-07-14 09:57:49</inptDt><br><rsrvtnPrceFileExistnceYn>Y</rsrvtnPrceFileExistnceYn><br><ntceInsttCd>1230137</ntceInsttCd><br><ntceInsttNm>조달청 대구지방조달청</ntceInsttNm><br><dminsttCd>Z021943</dminsttCd><br><dminsttNm>대구경북첨단의료산업진흥재단</dminsttNm><br><opengRsltNtcCntnts></opengRsltNtcCntnts><br></item><br></items><br><numOfRows>10</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

#### [개찰결과 공사 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 6 | 오퍼레이션명(국문) | 개찰결과 공사 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoCnstwk** |   |
|   | 오퍼레이션 설명 | 유찰, 개찰완료, 재입찰건에 대한 개찰결과를 제공하며 검색조건을 입력일시, 공고일시, 개찰일시, 입찰공고번호로하여 공사에 대한 나라장터 개찰결과 목록(입찰공고번호, 입찰공고명, 개찰일시, 참가업체수, 개찰업체정보, 진행구분코드명, 입력일시, 예비가격파일존재여부, 공고기관명, 수요기관명)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 0 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 0 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.입력일시, 2.공고일시,3.개찰일시,4.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 11 | 0 | R25BK00926014 | 검색하고자하는 입찰공고번호<br>조회구분 4인 경우 필수 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00926014 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 0 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 낭주중학교 인조 잔디 조성 및 담장 교체 공사 입찰 공고[긴급] | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| opengDt | 개찰일시 | 19 | 1 | 2025-07-01 11:00:00 | 조달업체가 제출한 입찰서를 개찰하는 일시  “YYYY-MM-DD HH:MM:SS” |
| prtcptCnum | 참가업체수 | 6 | 0 | 374 | 참가업체수 |
| opengCorpInfo | 개찰업체정보 | 500 | 1 | 유한회사 진무건설^4028138623^이세윤^462119000^88.393 | 개찰업체정보<br>다수 낙찰자의 경우 ”낙찰예정자 다수”와 개찰순위 1위의 투찰금액과 투찰율<br>을 보여줌<br>단일 낙찰자 의 경우 업체명과 사업자번호, 대표자명, 투찰금액, 투찰율을 보여줌<br>단, 협상에 의한 계약일 경우는 투찰금액,투찰율 안나옴 |
| progrsDivCdNm | 진행구분코드명 | 4 | 1 | 개찰완료 | 진행구분이<br>유찰, 개찰완료, 재입찰로 구분 됨 |
| inptDt | 입력일시 | 19 | 0 | 2025-07-01 11:08:48 | 입력일시 “YYYY-MM-DD HH:MM:SS” |
| rsrvtnPrceFileExistnceYn | 예비가격파일존재여부 | 1 | 1 | Y | 예비가격파일존재여부(Y/N) |
| ntceInsttCd | 공고기관코드 | 7 | 1 | 8462058 | 공고를 하는 기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 전북특별자치도교육청 전북특별자치도부안교육지원청 낭주중학교 | 수요기관의 의뢰를 받아 공고하는 기관의 명 |
| dminsttCd | 수요기관코드 | 7 | 0 | 8462058 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 전북특별자치도교육청 전북특별자치도부안교육지원청 낭주중학교 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| opengRsltNtcCntnts | 개찰결과공지내용 | 4000 | 0 | 개찰완료되었습니다. | 입찰공고번호, 입찰공고차수, 입찰분류번호, 재입찰번호에 해당하는 공지사항 내용 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoCnstwk?inqryDiv=4& bidNtceNo=R25BK00926014&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00926014</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>낭주중학교 인조 잔디 조성 및 담장 교체 공사 입찰 공고[긴급]</bidNtceNm><br><opengDt>2025-07-01 11:00:00</opengDt><br><prtcptCnum>374</prtcptCnum><br><opengCorpInfo>유한회사 진무건설^4028138623^이세윤^462119000^88.393</opengCorpInfo><br><progrsDivCdNm>개찰완료</progrsDivCdNm><br><inptDt>2025-07-01 11:08:48</inptDt><br><rsrvtnPrceFileExistnceYn>Y</rsrvtnPrceFileExistnceYn><br><ntceInsttCd>8462058</ntceInsttCd><br><ntceInsttNm>전북특별자치도교육청 전북특별자치도부안교육지원청 낭주중학교</ntceInsttNm><br><dminsttCd>8462058</dminsttCd><br><dminsttNm>전북특별자치도교육청 전북특별자치도부안교육지원청 낭주중학교</dminsttNm><br><opengRsltNtcCntnts></opengRsltNtcCntnts><br></item><br></items><br><numOfRows>999</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response |

#### [개찰결과 용역 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 7 | 오퍼레이션명(국문) | 개찰결과 용역 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoServc** |   |
|   | 오퍼레이션 설명 | 유찰, 개찰완료, 재입찰건에 대한 개찰결과를 제공하며 검색조건을 입력일시, 공고일시, 개찰일시, 입찰공고번호로하여 용역에 대한 나라장터 개찰결과 목록(입찰공고번호, 입찰공고명, 개찰일시, 참가업체수, 개찰업체정보, 진행구분코드명, 입력일시, 예비가격파일존재여부, 공고기관명, 수요기관명)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 0 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 0 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.입력일시, 2.공고일시,3.개찰일시,4.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 20250701000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 11 | 0 | R25BK00882586 | 검색하고자하는 입찰공고번호<br>조회구분 4인 경우 필수 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00882586 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 한국생명공학연구원 지역조직 중기 발전전략 수립 | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| opengDt | 개찰일시 | 19 | 1 | 2025-06-13 11:00:00 | 조달업체가 제출한 입찰서를 개찰하는 일시  “YYYY-MM-DD HH:MM:SS” |
| prtcptCnum | 참가업체수 | 6 | 0 | 2 | 참가업체수 |
| opengCorpInfo | 개찰업체정보 | 500 | 1 | (주식회사 과학기술전략연구소^5088702880^유경만^72000000^0 | 개찰업체정보<br>다수 낙찰자의 경우 ”낙찰예정자 다수”와 개찰순위 1위의 투찰금액과 투찰율을 보여줌<br>단일 낙찰자 의 경우 업체명과 사업자번호, 대표자명, 투찰금액, 투찰율을 보여줌<br>단, 협상에 의한 계약일 경우는 투찰금액, 투찰율 안나옴 |
| progrsDivCdNm | 진행구분코드명 | 4 | 1 | 개찰완료 | 진행구분이<br>유찰, 개찰완료, 재입찰로 구분 됨 |
| inptDt | 입력일시 | 19 | 0 | 2025-07-01 16:52:39 | 입력일시 “YYYY-MM-DD HH:MM:SS” |
| rsrvtnPrceFileExistnceYn | 예비가격파일존재여부 | 1 | 1 | N | 예비가격파일존재여부(Y/N) |
| ntceInsttCd | 공고기관코드 | 7 | 1 | Z004836 | 공고를 하는 기관의 코드로 행정자치부에서 부여한 기관코드임 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 한국생명공학연구원 | 수요기관의 의뢰를 받아 공고하는 기관의 명 |
| dminsttCd | 수요기관코드 | 7 | 0 | Z004836 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 한국생명공학연구원 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| opengRsltNtcCntnts | 개찰결과공지내용 | 4000 | 0 | 개찰결과공지내용 | 입찰공고번호, 입찰공고차수, 입찰분류번호, 재입찰번호에 해당하는 공지사항 내용 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoServc?inqryDiv=4& bidNtceNo=R25BK00882586&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00882586</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>한국생명공학연구원 지역조직 중기 발전전략 수립</bidNtceNm><br><opengDt>2025-06-13 11:00:00</opengDt><br><prtcptCnum>2</prtcptCnum><br><opengCorpInfo>주식회사 과학기술전략연구소^5088702880^유경만^72000000^0</opengCorpInfo><br><progrsDivCdNm>개찰완료</progrsDivCdNm><br><inptDt>2025-07-01 16:52:39</inptDt><br><rsrvtnPrceFileExistnceYn>N</rsrvtnPrceFileExistnceYn><br><ntceInsttCd>Z004836</ntceInsttCd><br><ntceInsttNm>한국생명공학연구원</ntceInsttNm><br><dminsttCd>Z004836</dminsttCd><br><dminsttNm>한국생명공학연구원</dminsttNm><br><opengRsltNtcCntnts></opengRsltNtcCntnts><br></item><br></items><br><numOfRows>10</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

<br>

#### [개찰결과 외자 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 8 | 오퍼레이션명(국문) | 개찰결과 외자 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoFrgcpt** |   |
|   | 오퍼레이션 설명 | 유찰, 개찰완료, 재입찰건에 대한 개찰결과를 제공하며 검색조건을 입력일시, 공고일시, 개찰일시, 입찰공고번호로하여 외자에 대한 나라장터 개찰결과 목록(입찰공고번호, 입찰공고명, 개찰일시, 참가업체수, 개찰업체정보, 진행구분코드명, 입력일시, 예비가격파일존재여부, 공고기관명, 수요기관명)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 0 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 0 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.입력일시, 2.공고일시,3.개찰일시,4.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2,3일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 11 | 0 | R25BK00916730 | 검색하고자하는 입찰공고번호<br>조회구분 4인 경우 필수 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00916730 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 외자조달요청(북부지원 유도결합플라즈마 질량분석기) | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| opengDt | 개찰일시 | 19 | 1 | 2025-07-01 13:00:00 | 조달업체가 제출한 입찰서를 개찰하는 일시  “YYYY-MM-DD HH:MM:SS” |
| prtcptCnum | 참가업체수 | 6 | 0 | 1 | 참가업체수 |
| opengCorpInfo | 개찰업체정보 | 500 | 1 | 써모피셔사이언티픽코리아 주식회사^1178146910^석수진^173500^0 | 개찰업체정보<br>다수 낙찰자의 경우 ”낙찰예정자 다수”와 개찰순위 1위의 투찰금액과 투찰율을 보여줌<br>단일 낙찰자 의 경우 업체명과 사업자번호, 대표자명, 투찰금액, 투찰율을 보여줌<br>단, 협상에 의한 계약일 경우는 투찰금액,투찰율 안나옴 |
| progrsDivCdNm | 진행구분코드명 | 4 | 1 | 개찰완료 | 진행구분이<br>유찰, 개찰완료, 재입찰로 구분 됨 |
| inptDt | 입력일시 | 19 | 0 | 2025-07-01 13:10:54 | 입력일시 “YYYY-MM-DD HH:MM:SS” |
| rsrvtnPrceFileExistnceYn | 예비가격파일존재여부 | 1 | 1 | N | 예비가격파일존재여부(Y/N) |
| ntceInsttCd | 공고기관코드 | 7 | 1 | 1230000 | 공고를 하는 기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 조달청 | 수요기관의 의뢰를 받아 공고하는 기관의 명 |
| dminsttCd | 수요기관코드 | 7 | 0 | 6440071 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 충청남도 보건환경연구원 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| opengRsltNtcCntnts | 개찰결과공지내용 | 4000 | 0 | 개찰결과공지내용 | 입찰공고번호, 입찰공고차수, 입찰분류번호, 재입찰번호에 해당하는 공지사항 내용 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoFrgcpt?inqryDiv=4& bidNtceNo=R25BK00916730&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00916730</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>외자조달요청(북부지원 유도결합플라즈마 질량분석기)</bidNtceNm><br><opengDt>2025-07-01 13:00:00</opengDt><br><prtcptCnum>1</prtcptCnum><br><opengCorpInfo>써모피셔사이언티픽코리아 주식회사^1178146910^석수진^173500^0</opengCorpInfo><br><progrsDivCdNm>개찰완료</progrsDivCdNm><br><inptDt>2025-07-01 13:10:54</inptDt><br><rsrvtnPrceFileExistnceYn>N</rsrvtnPrceFileExistnceYn><br><ntceInsttCd>1230000</ntceInsttCd><br><ntceInsttNm>조달청</ntceInsttNm><br><dminsttCd>6440071</dminsttCd><br><dminsttNm>충청남도 보건환경연구원</dminsttNm><br><opengRsltNtcCntnts></opengRsltNtcCntnts><br></item><br></items><br><numOfRows>999</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

<br>

#### [개찰결과 물품 예비가격상세 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 9 | 오퍼레이션명(국문) | 개찰결과 물품 예비가격상세 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoThngPreparPcDetail** |   |
|   | 오퍼레이션 설명 | 검색조건을 입력일시, 입찰공고번호로 물품에 대한 나라장터 개찰결과 예비가격상세 목록(입찰공고번호, 입찰공고명, 예정가격, 기초금액, 총예가건수, 복수예가순번, 기초예정가격, 추첨여부, 추첨횟수, 실개찰일시, 기초금액기준상위건수, 복수예비가격작성일시, 입력일시)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 0 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 0 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.입력일시, 2.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분이 1일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분이 1일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 11 | 0 | R25BK00845027 | 검색하고자하는 입찰공고번호<br>조회구분이 2일 경우 필수 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00845027 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | CT 및 X-ray 구매 | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| plnprc | 예정가격 | 21 | 0 | 270648500 | 예정가격은 계약담당공무원이 구매를 위한 경쟁입찰 또는 수의시담을 하기 전에 당해 계약 목적물의 특성 및 계약 여건 등을 고려하여 예산의 범위 내에서 경제적으로 구매가 가능하고 구매가격으로서 적정하다고 판단하여 정한 가격을 말하며 동 가격은 입찰 또는 시담에 의한 낙찰자 선정의 기준이고 계약체결에 대한 최고 상한 금액을 의미함.  (원화,원) |
| bssamt | 기초금액 | 21 | 0 | 270499000 | 예정가격 작성 과정에서 거래실례가격, 원가계산가격 등에 의하여 조사한 가격이나 설계가격에 대하여 계약담당공무원이 그 적정여부를 검토조정한 가격(원화,원) |
| totRsrvtnPrceNum | **총예가건수** | 2 | 0 | 15 | 총예가건수 |
| compnoRsrvtnPrceSno | **복수예가순번** | 6 | 0 | 7 | 복수예가순번 |
| bsisPlnprc | **기초예정가격** | 21 | 0 | 265727400 | 기초예정가격(원화,원) |
| drwtYn | **추첨여부** | 1 | 1 | Y | 추첨여부(Y/N) |
| drwtNum | **추첨횟수** | 22 | 0 | 1 | 추첨횟수 |
| bidwinrSlctnAplBssCntnts | 최종낙찰자선정적용기준내용 | 200 | 0 | 조달청 | 낙찰자선정적용기준내용 |
| rlOpengDt | **실개찰일시** | 19 | 0 | 2025-07-01 11:07:08 | 실제 개찰일시  “YYYY-MM-DD HH:MM:SS” |
| bssamtBssUpNum | 기초금액기준상위건수 | 2 | 0 | 8 | 기초금액기준상위건수 |
| compnoRsrvtnPrceMkngDt | **복수예비가격작성일시** | 19 | 0 | 2015-11-05  16:28:28 | 복수예비가격작성시각”YYYY-MM-DD HH:MM:SS” |
| inptDt | 입력일시 | 19 | 1 | 2025-07-01 11:07:08 | 입력일시 "YYYY-MM-DD HH:MM:SS" |
| PrearngPrcePurcnstcst | 예정가격순공사비 | 22 | 0 | 0 | 예정가격 중 순공사 원가(재료비,노무비,경비,및 이에 대한 부가가치세 합산금액) |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoThngPreparPcDetail?inqryDiv=2&bidNtceNo=R25BK00845027&bidNtceOrd=000&pageNo=1&numOfRows=15&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00845027</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>CT 및 X-ray 구매</bidNtceNm><br><plnprc>270648500</plnprc><br><bssamt>270499000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>1</compnoRsrvtnPrceSno><br><bsisPlnprc>268378300</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 11:07:08</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 10:47:30</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 11:07:08</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00845027</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>CT 및 X-ray 구매</bidNtceNm><br><plnprc>270648500</plnprc><br><bssamt>270499000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>2</compnoRsrvtnPrceSno><br><bsisPlnprc>273106700</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 11:07:08</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 10:47:30</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 11:07:08</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00845027</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>CT 및 X-ray 구매</bidNtceNm><br><plnprc>270648500</plnprc><br><bssamt>270499000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>3</compnoRsrvtnPrceSno><br><bsisPlnprc>267875200</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 11:07:08</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 10:47:30</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 11:07:08</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00845027</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>CT 및 X-ray 구매</bidNtceNm><br><plnprc>270648500</plnprc><br><bssamt>270499000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>4</compnoRsrvtnPrceSno><br><bsisPlnprc>269928300</bsisPlnprc><br><drwtYn>Y</drwtYn><br><drwtNum>1</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 11:07:08</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 10:47:30</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 11:07:08</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00845027</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>CT 및 X-ray 구매</bidNtceNm><br><plnprc>270648500</plnprc><br><bssamt>270499000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>5</compnoRsrvtnPrceSno><br><bsisPlnprc>274583600</bsisPlnprc><br><drwtYn>Y</drwtYn><br><drwtNum>1</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 11:07:08</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 10:47:30</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 11:07:08</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00845027</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>CT 및 X-ray 구매</bidNtceNm><br><plnprc>270648500</plnprc><br><bssamt>270499000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>6</compnoRsrvtnPrceSno><br><bsisPlnprc>275706200</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 11:07:08</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 10:47:30</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 11:07:08</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00845027</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>CT 및 X-ray 구매</bidNtceNm><br><plnprc>270648500</plnprc><br><bssamt>270499000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>7</compnoRsrvtnPrceSno><br><bsisPlnprc>265727400</bsisPlnprc><br><drwtYn>Y</drwtYn><br><drwtNum>1</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 11:07:08</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 10:47:30</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 11:07:08</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00845027</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>CT 및 X-ray 구매</bidNtceNm><br><plnprc>270648500</plnprc><br><bssamt>270499000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>8</compnoRsrvtnPrceSno><br><bsisPlnprc>268984300</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 11:07:08</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 10:47:30</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 11:07:08</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00845027</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>CT 및 X-ray 구매</bidNtceNm><br><plnprc>270648500</plnprc><br><bssamt>270499000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>9</compnoRsrvtnPrceSno><br><bsisPlnprc>270512600</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 11:07:08</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 10:47:30</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 11:07:08</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00845027</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>CT 및 X-ray 구매</bidNtceNm><br><plnprc>270648500</plnprc><br><bssamt>270499000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>10</compnoRsrvtnPrceSno><br><bsisPlnprc>273842400</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 11:07:08</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 10:47:30</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 11:07:08</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br></items><br><numOfRows>10</numOfRows><br><pageNo>1</pageNo><br><totalCount>15</totalCount><br></body><br></response> |

#### [개찰결과 공사 예비가격상세 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 10 | 오퍼레이션명(국문) | 개찰결과 공사 예비가격상세 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoCnstwkPreparPcDetail** |   |
|   | 오퍼레이션 설명 | 검색조건을 등록일시, 입찰공고번호로 공사에 대한 나라장터 개찰결과 예비가격상세 목록(입찰공고번호, 입찰공고명, 예정가격, 기초금액, 총예가건수, 복수예가순번, 기초예정가격, 추첨여부, 추첨횟수, 실개찰일시, 기초금액기준상위건수, 복수예비가격작성일시, 입력일시)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.입력일시, 2.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분이 1일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분이 1일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 11 | 0 | R25BK00888538 | 검색하고자하는 입찰공고번호<br>조회구분이 2일 경우 필수 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00888538 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 003 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 0 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동) | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| plnprc | 예정가격 | 21 | 0 | 1773240950 | 예정가격은 계약담당공무원이 구매를 위한 경쟁입찰 또는 수의시담을 하기 전에 당해 계약 목적물의 특성 및 계약 여건 등을 고려하여 예산의 범위 내에서 경제적으로 구매가 가능하고 구매가격으로서 적정하다고 판단하여 정한 가격을 말하며 동 가격은 입찰 또는 시담에 의한 낙찰자 선정의 기준이고 계약체결에 대한 최고 상한 금액을 의미함.  (원화,원) |
| bssamt | 기초금액 | 21 | 0 | 1797931000 | 예정가격 작성 과정에서 거래실례가격, 원가계산가격 등에 의하여 조사한 가격이나 설계가격에 대하여 계약담당공무원이 그 적정여부를 검토조정한 가격(원화,원) |
| totRsrvtnPrceNum | 총예가건수 | 2 | 0 | 15 | 총예가건수 |
| compnoRsrvtnPrceSno | 복수예가순번 | 6 | 0 | 1 | 복수예가순번 |
| bsisPlnprc | 기초예정가격 | 21 | 0 | 1825493300 | 기초예정가격(원화,원) |
| drwtYn | 추첨여부 | 1 | 1 | Y | 추첨여부(Y/N) |
| drwtNum | **추첨횟수** | 22 | 0 | 11 | 추첨횟수 |
| bidwinrSlctnAplBssCntnts | 최종낙찰자선정적용기준내용 | 200 | 0 | 행자부 | 낙찰자선정적용기준내용 |
| rlOpengDt | 실개찰일시 | 19 | 0 | 2025-07-01 13:14:24 | 실제 개찰일시  “YYYY-MM-DD HH:MM:SS” |
| bssamtBssUpNum | 기초금액기준상위건수 | 2 | 0 | 7 | 기초금액기준상위건수 |
| compnoRsrvtnPrceMkngDt | 복수예비가격작성일시 | 19 | 0 | 2025-07-01 13:07:31 | 복수예비가격작성시각”YYYY-MM-DD HH:MM:SS” |
| inptDt | 입력일시 | 19 | 1 | 2025-07-01 13:14:24 | 입력일시 "YYYY-MM-DD HH:MM:SS" |
| PrearngPrcePurcnstcst | 예정가격순공사비 | 22 | 0 | 1470841837 | 예정가격 중 순공사 원가(재료비,노무비,경비,및 이에 대한 부가가치세 합산금액) |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoCnstwkPreparPcDetail?inqryDiv=2&bidNtceNo=R25BK00888538&bidNtceOrd=003&pageNo=1&numOfRows=15&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>1</compnoRsrvtnPrceSno><br><bsisPlnprc>1825493300</bsisPlnprc><br><drwtYn>Y</drwtYn><br><drwtNum>11</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>2</compnoRsrvtnPrceSno><br><bsisPlnprc>1759904800</bsisPlnprc><br><drwtYn>Y</drwtYn><br><drwtNum>13</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>3</compnoRsrvtnPrceSno><br><bsisPlnprc>1757387700</bsisPlnprc><br><drwtYn>Y</drwtYn><br><drwtNum>9</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>4</compnoRsrvtnPrceSno><br><bsisPlnprc>1772418400</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>7</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>5</compnoRsrvtnPrceSno><br><bsisPlnprc>1780023700</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>7</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>6</compnoRsrvtnPrceSno><br><bsisPlnprc>1750178000</bsisPlnprc><br><drwtYn>Y</drwtYn><br><drwtNum>11</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>7</compnoRsrvtnPrceSno><br><bsisPlnprc>1808377000</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>4</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>8</compnoRsrvtnPrceSno><br><bsisPlnprc>1830293800</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>9</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>9</compnoRsrvtnPrceSno><br><bsisPlnprc>1804133900</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>9</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>10</compnoRsrvtnPrceSno><br><bsisPlnprc>1769775500</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>8</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>11</compnoRsrvtnPrceSno><br><bsisPlnprc>1785381500</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>7</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>12</compnoRsrvtnPrceSno><br><bsisPlnprc>1837413600</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>5</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>13</compnoRsrvtnPrceSno><br><bsisPlnprc>1795306100</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>7</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>14</compnoRsrvtnPrceSno><br><bsisPlnprc>1848381000</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>9</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00888538</bidNtceNo><br><bidNtceOrd>003</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>하동군수협 유통단계 위생안전체계 구축사업 (친환경 위판장) (건축,기계,냉동)</bidNtceNm><br><plnprc>1773240950</plnprc><br><bssamt>1797931000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>15</compnoRsrvtnPrceSno><br><bsisPlnprc>1815730600</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>4</drwtNum><br><bidwinrSlctnAplBssCntnts>행자부</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:14:24</rlOpengDt><br><bssamtBssUpNum>7</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:07:31</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:14:24</inptDt><br><PrearngPrcePurcnstcst>1470841837</PrearngPrcePurcnstcst><br></item><br></items><br><numOfRows>500</numOfRows><br><pageNo>1</pageNo><br><totalCount>15</totalCount><br></body><br></response> |

<br>

#### [개찰결과 용역 예비가격상세 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 11 | 오퍼레이션명(국문) | 개찰결과 용역 예비가격상세 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoServcPreparPcDetail** |   |
|   | 오퍼레이션 설명 | 검색조건을 등록일시, 입찰공고번호로 용역에 대한 나라장터 개찰결과 예비가격상세 목록(입찰공고번호, 입찰공고명, 예정가격, 기초금액, 총예가건수, 복수예가순번, 기초예정가격, 추첨여부, 추첨횟수, 실개찰일시, 기초금액기준상위건수, 복수예비가격작성일시, 입력일시)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.입력일시, 2.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분이 1일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분이 1일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 11 | 0 | R25BK00811340 | 검색하고자하는 입찰공고번호<br>조회구분이 2일 경우 필수 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00811340 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 0 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역 | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| plnprc | 예정가격 | 21 | 0 | 404158750 | 예정가격은 계약담당공무원이 구매를 위한 경쟁입찰 또는 수의시담을 하기 전에 당해 계약 목적물의 특성 및 계약 여건 등을 고려하여 예산의 범위 내에서 경제적으로 구매가 가능하고 구매가격으로서 적정하다고 판단하여 정한 가격을 말하며 동 가격은 입찰 또는 시담에 의한 낙찰자 선정의 기준이고 계약체결에 대한 최고 상한 금액을 의미함.  (원화,원) |
| bssamt | 기초금액 | 21 | 0 | 404282000 | 예정가격 작성 과정에서 거래실례가격, 원가계산가격 등에 의하여 조사한 가격이나 설계가격에 대하여 계약담당공무원이 그 적정여부를 검토조정한 가격(원화,원) |
| totRsrvtnPrceNum | 총예가건수 | 2 | 0 | 15 | 총예가건수 |
| compnoRsrvtnPrceSno | 복수예가순번 | 6 | 0 | 4 | 복수예가순번 |
| bsisPlnprc | 기초예정가격 | 21 | 0 | 405745600 | 기초예정가격(원화,원) |
| drwtYn | 추첨여부 | 1 | 1 | Y | 추첨여부(Y/N) |
| drwtNum | **추첨횟수** | 22 | 0 | 1 | 추첨횟수 |
| bidwinrSlctnAplBssCntnts | 최종낙찰자선정적용기준내용 | 200 | 0 | 조달청 | 낙찰자선정적용기준내용 |
| rlOpengDt | 실개찰일시 | 19 | 0 | 2025-07-01 13:54:13 | 실제 개찰일시  “YYYY-MM-DD HH:MM:SS” |
| bssamtBssUpNum | 기초금액기준상위건수 | 2 | 0 | 8 | 기초금액기준상위건수 |
| compnoRsrvtnPrceMkngDt | 복수예비가격작성일시 | 19 | 0 | 2025-07-01 13:53:36 | 복수예비가격작성시각”YYYY-MM-DD HH:MM:SS” |
| inptDt | 입력일시 | 19 | 1 | 2025-07-01 13:54:13 | 입력일시 "YYYY-MM-DD HH:MM:SS" |
| PrearngPrcePurcnstcst | 예정가격순공사비 | 22 | 0 | 0 | 예정가격 중 순공사 원가(재료비,노무비,경비,및 이에 대한 부가가치세 합산금액) |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoServcPreparPcDetail?inqryDiv=2&bidNtceNo=R25BK00811340&bidNtceOrd=000&pageNo=1&numOfRows=15&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>1</compnoRsrvtnPrceSno><br><bsisPlnprc>409780300</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>2</compnoRsrvtnPrceSno><br><bsisPlnprc>408587700</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>3</compnoRsrvtnPrceSno><br><bsisPlnprc>400930600</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>4</compnoRsrvtnPrceSno><br><bsisPlnprc>405745600</bsisPlnprc><br><drwtYn>Y</drwtYn><br><drwtNum>1</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>5</compnoRsrvtnPrceSno><br><bsisPlnprc>407184800</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>6</compnoRsrvtnPrceSno><br><bsisPlnprc>402782200</bsisPlnprc><br><drwtYn>Y</drwtYn><br><drwtNum>1</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>7</compnoRsrvtnPrceSno><br><bsisPlnprc>399394300</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>8</compnoRsrvtnPrceSno><br><bsisPlnprc>397482000</bsisPlnprc><br><drwtYn>Y</drwtYn><br><drwtNum>3</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>9</compnoRsrvtnPrceSno><br><bsisPlnprc>406659200</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>10</compnoRsrvtnPrceSno><br><bsisPlnprc>401941300</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>1</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>11</compnoRsrvtnPrceSno><br><bsisPlnprc>396928200</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>12</compnoRsrvtnPrceSno><br><bsisPlnprc>410625200</bsisPlnprc><br><drwtYn>Y</drwtYn><br><drwtNum>2</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>13</compnoRsrvtnPrceSno><br><bsisPlnprc>399774300</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>1</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>14</compnoRsrvtnPrceSno><br><bsisPlnprc>411644000</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br><item><br><bidNtceNo>R25BK00811340</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>천안시 성남면 및 수신면 기초생활거점조성사업 기본계획수립 용역</bidNtceNm><br><plnprc>404158750</plnprc><br><bssamt>404282000</bssamt><br><totRsrvtnPrceNum>15</totRsrvtnPrceNum><br><compnoRsrvtnPrceSno>15</compnoRsrvtnPrceSno><br><bsisPlnprc>404419500</bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>1</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:54:13</rlOpengDt><br><bssamtBssUpNum>8</bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt>2025-07-01 13:53:36</compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:54:13</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br></items><br><numOfRows>999</numOfRows><br><pageNo>1</pageNo><br><totalCount>15</totalCount><br></body><br></response> |

#### [개찰결과 외자 예비가격상세 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 12 | 오퍼레이션명(국문) | 개찰결과 외자 예비가격상세 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoFrgcptPreparPcDetail** |   |
|   | 오퍼레이션 설명 | 검색조건을 등록일시, 입찰공고번호로 외자에 대한 나라장터 개찰결과 외자 예비가격상세 목록(입찰공고번호, 입찰공고명, 예정가격, 기초금액, 총예가건수, 복수예가순번, 기초예정가격, 추첨여부, 추첨횟수, 실개찰일시, 기초금액기준상위건수, 복수예비가격작성일시, 입력일시)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.입력일시, 2.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분이 1일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분이 1일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 11 | 0 | R25BK00883422 | 검색하고자하는 입찰공고번호<br>조회구분이 2일 경우 필수 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00883422 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 호흡용 고압공기압축기 고정형 | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| plnprc | 예정가격 | 21 | 0 | 0 | 예정가격은 계약담당공무원이 구매를 위한 경쟁입찰 또는 수의시담을 하기 전에 당해 계약 목적물의 특성 및 계약 여건 등을 고려하여 예산의 범위 내에서 경제적으로 구매가 가능하고 구매가격으로서 적정하다고 판단하여 정한 가격을 말하며 동 가격은 입찰 또는 시담에 의한 낙찰자 선정의 기준이고 계약체결에 대한 최고 상한 금액을 의미함.  (원화,원) |
| bssamt | 기초금액 | 21 | 0 | 0 | 예정가격 작성 과정에서 거래실례가격, 원가계산가격 등에 의하여 조사한 가격이나 설계가격에 대하여 계약담당공무원이 그 적정여부를 검토조정한 가격(원화,원) |
| totRsrvtnPrceNum | 총예가건수 | 2 | 0 | 0 | 총예가건수 |
| compnoRsrvtnPrceSno | 복수예가순번 | 6 | 0 | 0 | 복수예가순번 |
| bsisPlnprc | 기초예정가격 | 21 | 0 | 0 | 기초예정가격(원화,원) |
| drwtYn | 추첨여부 | 1 | 1 | N | 추첨여부(Y/N) |
| drwtNum | **추첨횟수** | 22 | 0 | 0 | 추첨횟수 |
| bidwinrSlctnAplBssCntnts | 최종낙찰자선정적용기준내용 | 200 | 0 | 조달청 | 낙찰자선정적용기준내용 |
| rlOpengDt | 실개찰일시 | 19 | 0 | 2025-07-01 13:35:42 | 실제 개찰일시  “YYYY-MM-DD HH:MM:SS” |
| bssamtBssUpNum | 기초금액기준상위건수 | 2 | 0 | 0 | 기초금액기준상위건수 |
| compnoRsrvtnPrceMkngDt | 복수예비가격작성일시 | 19 | 0 | 2025-07-01 13:35:42 | 복수예비가격작성시각”YYYY-MM-DD HH:MM:SS” |
| inptDt | 입력일시 | 19 | 1 | 2025-07-01 13:35:42 | 입력일시 "YYYY-MM-DD HH:MM:SS" |
| PrearngPrcePurcnstcst | 예정가격순공사비 | 22 | 0 | 0 | 예정가격 중 순공사 원가(재료비,노무비,경비,및 이에 대한 부가가치세 합산금액) |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoFrgcptPreparPcDetail?inqryDiv=2& bidNtceNo= R25BK00883422& bidNtceOrd=000&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00883422</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>호흡용 고압공기압축기 고정형</bidNtceNm><br><plnprc></plnprc><br><bssamt></bssamt><br><totRsrvtnPrceNum></totRsrvtnPrceNum><br><compnoRsrvtnPrceSno></compnoRsrvtnPrceSno><br><bsisPlnprc></bsisPlnprc><br><drwtYn>N</drwtYn><br><drwtNum>0</drwtNum><br><bidwinrSlctnAplBssCntnts>조달청</bidwinrSlctnAplBssCntnts><br><rlOpengDt>2025-07-01 13:35:42</rlOpengDt><br><bssamtBssUpNum></bssamtBssUpNum><br><compnoRsrvtnPrceMkngDt></compnoRsrvtnPrceMkngDt><br><inptDt>2025-07-01 13:35:42</inptDt><br><PrearngPrcePurcnstcst></PrearngPrcePurcnstcst><br></item><br></items><br><numOfRows>999</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

<br>

#### [개찰결과 개찰완료 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 13 | 오퍼레이션명(국문) | 개찰결과 개찰완료 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoOpengCompt** |   |
|   | 오퍼레이션 설명 | 물품, 공사, 용역, 외자의 개찰완료된 건에 대하여 최종낙찰업체 및 투찰업체의 개찰순위 정보를 제공하며 검색조건을 입찰공고번호하여 나라장터 개찰결과 개찰완료 목록(개찰결과구분명, 입찰공고번호, 입찰공고차수, 입찰분류번호, 재입찰번호, 개찰순위, 최종낙찰업체사업자등록번호, 최종낙찰업체명, 최종낙찰업체대표자명, 투찰금액, 투찰룰, 비고, 공종별입찰금액URL), 추첨번호1, 추첨번호2, 투찰일시 등 개찰완료 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK01027145 | 검색하고자하는 입찰공고번호 |
| bidNtceOrd | 입찰공고차수 | 2 | 0 | 002 | 검색하고자하는 입찰공고차수 |
| bidClsfcNo | 입찰분류번호 | 5 | 0 | 0 | 검색하고자하는 입찰분류번호 |
| rbidNo | 재입찰번호 | 3 | 0 | 000 | 검색하고자하는 재입찰번호 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 6 | 데이터 총 개수 |
| opengRsltDivNm | 개찰결과구분명 | 30 | 1 | 개찰완료 | 해당 공고건에 대한 개찰결과를 구분하는 것으로 개찰이 완료되었는지, 유찰되었는지, 재입찰 할것인지 등을 구분하는 명으로 이 오퍼레이션은 개찰완료인 정보 조회 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK01027145 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 002 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 0 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| opengRank | 개찰순위 | 7 | 0 | 1 | 개찰순위는 협상기술능력 평가점수와 입찰가격 평가점수의 합산하여 고득점 순에 따라 결정되는 순위로 협상에 의한 계약일 경우, 협상순위를 의미함 |
| **prcbdrBizno** | 투찰업체**사업자등록번호** | 10 | 1 | 6438701544 | 협상이 완료 후 투찰업체의 사업자등록번호임 |
| **prcbdrNm** | 투찰업체명 | 200 | 0 | 주식회사 예신뷰 | 투찰업체의 명으로 개찰결과구분명이 “개찰완료”일 경우 필수 입력 항목임 |
| **prcbdrCeoNm** | 투찰업체대표자명 | 35 | 0 | 최인아 | 투찰업체의 대표자명으로 개찰결과구분명이 “개찰완료”일 경우 필수 입력 항목임 |
| bidprcAmt | 투찰금액 | 21 | 0 | 100111000 | 투찰한 금액(원화,원) |
| bidprcrt | 투찰률 | 18 | 0 | 91.01 | 예정가격에 대한 투찰금액의 비율로 투찰금액/예정가격 *100 임(%) |
| rmrk | 비고 | 200 | 0 | 낙찰 | 개찰완료내역의 비고 |
| cnsttyAccotBidAmtUrl | 공종별입찰금액URL | 150 | 0 | N/A | *차세대 나라장터 개편 이후 제공 불가 |
| drwtNo1 | 추첨번호1 | 3 | 0 | 10 | 추첨번호1 |
| drwtNo2 | 추첨번호2 | 3 | 0 | 02 | 추첨번호2 |
| bidprcDt | 투찰일시 | 19 | 0 | 2025-09-16 09:40:35 | 투찰일시 "YYYY-MM-DD HH:MM:SS" |
| bidPrceEvlVal | 입찰가격점수 | 25 | 0 | 9.5894 | 낙찰방법이 협상에 의한 계약의 입찰가격평가점수 |
| techEvlNaturVal | 기술평가원점수 | 25 | 0 | 0 | 낙찰방법이 협상에 의한 계약의 차등점수제적용의 기술평가 원점수 |
| techEvlVal | 기술평가점수 | 25 | 0 | 81.5 | 낙찰방법이 협상에 의한 계약의 기술평가점수<br>* 차등점수제적용의 경우 기술평가총점수 |
| totalEvlAmtVal | 종합평가점수 | 25 | 0 | 91.0894 | 낙찰방법이 협상에 의한 계약의 종합평가점수 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoOpengCompt?bidNtceNo= R25BK01027145 &bidNtceOrd=002&bidClsfcNo=0&rbidNo=000&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><opengRsltDivNm>개찰완료</opengRsltDivNm><br><bidNtceNo>R25BK01027145</bidNtceNo><br><bidNtceOrd>002</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><opengRank>1</opengRank><br><prcbdrBizno>6438701544</prcbdrBizno><br><prcbdrNm>주식회사 예신뷰</prcbdrNm><br><prcbdrCeoNm>최인아</prcbdrCeoNm><br><bidprcAmt>100111000</bidprcAmt><br><bidprcrt>91.01</bidprcrt><br><rmrk></rmrk><br><cnsttyAccotBidAmtUrl></cnsttyAccotBidAmtUrl><br><drwtNo1></drwtNo1><br><drwtNo2></drwtNo2><br><bidprcDt>2025-09-16 09:40:35</bidprcDt><br><bidPrceEvlVal>9.5894</bidPrceEvlVal><br><techEvlVal>81.5</techEvlVal><br><totalEvlAmtVal>91.0894</totalEvlAmtVal><br><techEvlNaturVal></techEvlNaturVal><br></item><br><item><br><opengRsltDivNm>개찰완료</opengRsltDivNm><br><bidNtceNo>R25BK01027145</bidNtceNo><br><bidNtceOrd>002</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><opengRank>2</opengRank><br><prcbdrBizno>1078648444</prcbdrBizno><br><prcbdrNm>주식회사 명진씨앤피</prcbdrNm><br><prcbdrCeoNm>최영무</prcbdrCeoNm><br><bidprcAmt>98000000</bidprcAmt><br><bidprcrt>89.09</bidprcrt><br><rmrk></rmrk><br><cnsttyAccotBidAmtUrl></cnsttyAccotBidAmtUrl><br><drwtNo1></drwtNo1><br><drwtNo2></drwtNo2><br><bidprcDt>2025-09-16 09:40:35</bidprcDt><br><bidPrceEvlVal>9.7959</bidPrceEvlVal><br><techEvlVal>80.3</techEvlVal><br><totalEvlAmtVal>90.0959</totalEvlAmtVal><br><techEvlNaturVal></techEvlNaturVal><br></item><br><item><br><opengRsltDivNm>개찰완료</opengRsltDivNm><br><bidNtceNo>R25BK01027145</bidNtceNo><br><bidNtceOrd>002</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><opengRank>3</opengRank><br><prcbdrBizno>1051842348</prcbdrBizno><br><prcbdrNm>칼리그램</prcbdrNm><br><prcbdrCeoNm>김용운</prcbdrCeoNm><br><bidprcAmt>100000000</bidprcAmt><br><bidprcrt>90.909</bidprcrt><br><rmrk></rmrk><br><cnsttyAccotBidAmtUrl></cnsttyAccotBidAmtUrl><br><drwtNo1></drwtNo1><br><drwtNo2></drwtNo2><br><bidprcDt>2025-09-16 09:40:35</bidprcDt><br><bidPrceEvlVal>9.6</bidPrceEvlVal><br><techEvlVal>78.3</techEvlVal><br><totalEvlAmtVal>87.9</totalEvlAmtVal><br><techEvlNaturVal></techEvlNaturVal><br></item><br><item><br><opengRsltDivNm>개찰완료</opengRsltDivNm><br><bidNtceNo>R25BK01027145</bidNtceNo><br><bidNtceOrd>002</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><opengRank>4</opengRank><br><prcbdrBizno>1160178265</prcbdrBizno><br><prcbdrNm>경성문화사</prcbdrNm><br><prcbdrCeoNm>박진태</prcbdrCeoNm><br><bidprcAmt>100000000</bidprcAmt><br><bidprcrt>90.909</bidprcrt><br><rmrk></rmrk><br><cnsttyAccotBidAmtUrl></cnsttyAccotBidAmtUrl><br><drwtNo1></drwtNo1><br><drwtNo2></drwtNo2><br><bidprcDt>2025-09-16 09:40:35</bidprcDt><br><bidPrceEvlVal>9.6</bidPrceEvlVal><br><techEvlVal>78.2</techEvlVal><br><totalEvlAmtVal>87.8</totalEvlAmtVal><br><techEvlNaturVal></techEvlNaturVal><br></item><br><item><br><opengRsltDivNm>개찰완료</opengRsltDivNm><br><bidNtceNo>R25BK01027145</bidNtceNo><br><bidNtceOrd>002</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><opengRank>5</opengRank><br><prcbdrBizno>1058763392</prcbdrBizno><br><prcbdrNm>주식회사 도서출판알투스</prcbdrNm><br><prcbdrCeoNm>손은주</prcbdrCeoNm><br><bidprcAmt>96000000</bidprcAmt><br><bidprcrt>87.272</bidprcrt><br><rmrk></rmrk><br><cnsttyAccotBidAmtUrl></cnsttyAccotBidAmtUrl><br><drwtNo1></drwtNo1><br><drwtNo2></drwtNo2><br><bidprcDt>2025-09-16 09:40:35</bidprcDt><br><bidPrceEvlVal>10</bidPrceEvlVal><br><techEvlVal>75.7</techEvlVal><br><totalEvlAmtVal>85.7</totalEvlAmtVal><br><techEvlNaturVal></techEvlNaturVal><br></item><br><item><br><opengRsltDivNm>개찰완료</opengRsltDivNm><br><bidNtceNo>R25BK01027145</bidNtceNo><br><bidNtceOrd>002</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><opengRank>6</opengRank><br><prcbdrBizno>3123161127</prcbdrBizno><br><prcbdrNm>디자인소나무</prcbdrNm><br><prcbdrCeoNm>유영주</prcbdrCeoNm><br><bidprcAmt>108520000</bidprcAmt><br><bidprcrt>98.654</bidprcrt><br><rmrk></rmrk><br><cnsttyAccotBidAmtUrl></cnsttyAccotBidAmtUrl><br><drwtNo1></drwtNo1><br><drwtNo2></drwtNo2><br><bidprcDt>2025-09-16 09:40:35</bidprcDt><br><bidPrceEvlVal>8.8463</bidPrceEvlVal><br><techEvlVal>68.7</techEvlVal><br><totalEvlAmtVal>77.5463</totalEvlAmtVal><br><techEvlNaturVal></techEvlNaturVal><br></item><br></items><br><numOfRows>10</numOfRows><br><pageNo>1</pageNo><br><totalCount>6</totalCount><br></body><br></response> |

<br>

#### [개찰결과 유찰 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 14 | 오퍼레이션명(국문) | 개찰결과 유찰 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoFailing** |   |
|   | 오퍼레이션 설명 | 검색조건을 입찰공고번호 입력하여 물품, 공사, 용역, 외자의 나라장터 개찰결과 유찰 목록(개찰결과구분명, 입찰공고번호, 입찰공고차수, 입찰분류번호, 재입찰번호, 유찰사유)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00936962 | 검색하고자하는 입찰공고번호 |
| bidNtceOrd | 입찰공고차수 | 3 | 0 | 000 | 검색하고자하는 입찰공고차수 |
| bidClsfcNo | 입찰분류번호 | 5 | 0 | 1 | 검색하고자하는 입찰분류번호 |
| rbidNo | 재입찰번호 | 3 | 0 | 000 | 검색하고자하는 재입찰번호 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| opengRsltDivNm | 개찰결과구분명 | 30 | 1 | 유찰 | 해당 공고건에 대한 개찰결과를 구분하는 것으로 개찰이 완료되었는지, 유찰되었는지, 재입찰 할것인지 등을 구분하는 명으로 이 오퍼레이션은 유찰인 정보 조회 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00936962 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| nobidRsn | **유찰사유** | 200 | 0 | 단독응찰 | 유찰사유 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoFailing?bidNtceNo=R25BK00936962&bidNtceOrd=000&bidClsfcNo=1&rbidNo=000&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><opengRsltDivNm>유찰</opengRsltDivNm><br><bidNtceNo>R25BK00936962</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><nobidRsn>단독응찰</nobidRsn><br></item><br></items><br><numOfRows>10</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

#### [개찰결과 재입찰 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 15 | 오퍼레이션명(국문) | 개찰결과 재입찰 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoRebid** |   |
|   | 오퍼레이션 설명 | 검색조건을 입찰공고번호 입력하여 물품, 공사, 용역, 외자의 나라장터 개찰결과 재입찰 목록(개찰결과구분명, 입찰공고번호, 입찰공고차수, 입찰분류번호, 재입찰번호, 입찰마감일시, 개찰일시, 재입찰사유, 공동수급협정마감일시)을 조회. |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00922094 | 검색하고자하는 입찰공고번호 |
| bidNtceOrd | 입찰공고차수 | 2 | 0 | 000 | 검색하고자하는 입찰공고차수 |
| bidClsfcNo | 입찰분류번호 | 5 | 0 | 1 | 검색하고자하는 입찰분류번호 |
| rbidNo | 재입찰번호 | 3 | 0 | 000 | 검색하고자하는 재입찰번호 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| opengRsltDivNm | 개찰결과구분명 | 30 | 1 | 재입찰 | 해당 공고건에 대한 개찰결과를 구분하는 것으로 개찰이 완료되었는지, 유찰되었는지, 재입찰 할것인지 등을 구분하는 명으로 이 오퍼레이션은 재입찰인 정보 조회 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00922094 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 2 | 1 | 001 | 재입찰이 발생되었을 경우 증가되는 재입찰번호 |
| bidClseDt | 입찰마감일시 | 19 | 1 | 2025-07-15 18:00:00 | 입찰마감일시  “YYYY-MM-DD HH:MM:SS” |
| opengDt | 개찰일시 | 19 | 1 | 2025-07-15 19:00:00 | 조달업체가 제출한 입찰서를 개찰하는 일시  “YYYY-MM-DD HH:MM:SS” |
| rbidRsn | 재입찰사유 | 200 | 0 | 낙찰자 없음 | 재입찰사유 |
| cmmnSpldmdAgrmntClseDt | **공동수급혐정마감일시** | 19 | 0 | 2025-07-15 18:00:00 | 공동수급혐정마감일시 “YYYY-MM-DD HH:MM:SS” |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getOpengResultListInfoRebid?bidNtceNo=R25BK00922094&bidNtceOrd=000&bidClsfcNo=1&rbidNo=000&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><opengRsltDivNm>재입찰</opengRsltDivNm><br><bidNtceNo>R25BK00922094</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>001</rbidNo><br><bidClseDt>2025-07-15 18:00:00</bidClseDt><br><opengDt>2025-07-15 19:00:00</opengDt><br><rbidRsn>낙찰자 없음</rbidRsn><br><cmmnSpldmdAgrmntClseDt></cmmnSpldmdAgrmntClseDt><br></item><br></items><br><numOfRows>10</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response |

<br>

#### [나라장터 검색조건에 의한 낙찰된 목록 현황 물품조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 16 | 오퍼레이션명(국문) | 나라장터 검색조건에 의한 낙찰된 목록 현황 물품조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getScsbidListSttusThngPPSSrch** |   |
|   | 오퍼레이션 설명 | 검색조건을 공고일시, 개찰일시, 입찰공고번호, 입찰공고명, 공고기관코드, 공고기관명, 수요기관코드, 수요기관명, 참조번호, 참가제한지역코드, 참가제한지역명, 업종코드, 업종명, 추정가격시작, 추정가격종료, 세부품명번호, 다수공급경쟁자여부, 조달요청번호, 국제구분코드로 물품에 대한 나라장터 최종낙찰자 목록(입찰공고번호, 입찰공고명, 참가업체수, 최종낙찰업체명, 사업자번호, 최종낙찰률, 실개찰일시, 수요기관)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |   |
| --- | --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |   |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |   |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |   |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |   |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1:공고게시일시, 2:개찰일시, 3:입찰공고번호 |   |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자 하는 조회시작일시 "YYYYMMDDHHMM"<br>조회구분이 '1'인 경우 공고게시일시 필수, '2'인 경우 개찰일시 필수 |   |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자 하는 조회종료일시 "YYYYMMDDHHMM"<br>조회구분이 '1'인 경우 공고게시일시 필수, '2'인 경우 개찰일시 필수 |   |
| bidNtceNo | 입찰공고번호 | 40 | 0 | R25BK00965123 | 검색하고자하는 입찰공고번호<br>조회구분이 '3'인 경우 필수 |   |
| bidNtceNm | 입찰공고명 | 1000 | 0 | 혁신육아복합센터 건립공사(기계) 관급자재(간접가열보일러) | 검색하고자하는 공고명<br>※ 공고명 일부 입력시에도 조회 가능 |   |
| ntceInsttCd | 공고기관코드 | 7 | 0 | 6280147 | 검색하고자하는 공고기관코드 |   |
| ntceInsttNm | 공고기관명 | 200 | 0 | 인천광역시 종합건설본부 | 검색하고자하는 공고기관명<br>※ 공고기관명 일부 입력시에도 조회 가능 |   |
| dminsttCd | 수요기관코드 | 7 | 0 | 6280147 | 검색하고자하는 수요기관코드<br>행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드 입력<br>행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드 입력 |   |
| dminsttNm | 수요기관명 | 200 | 0 | 인천광역시 종합건설본부 | 검색하고자하는 수요기관명<br>※ 수요기관명 일부 입력시에도 조회 가능 |   |
| refNo | 참조번호 | 105 | 0 | 제2025 | 검색하고자하는 참조번호 |   |
| prtcptLmtRgnCd | 참가제한지역코드 | 2 | 0 | 00 | 검색하고자하는 참가제한지역코드<br>11 : 서울특별시<br>26 : 부산광역시<br>27 : 대구광역시<br>28 : 인천광역시<br>29 : 광주광역시<br>30 : 대전광역시<br>31 : 울산광역시<br>36 : 세종특별자치시<br>41 : 경기도<br>42 : 강원도<br>43 : 충청북도<br>44 : 충청남도<br>45 : 전라북도<br>46 : 전라남도<br>47 : 경상북도<br>48 : 경상남도<br>50 : 제주도<br>51    : 강원특별자치도<br>52    : 전북특별자치도<br>99 : 기타<br>00: 전국<br>*전국 : 지역제한을 설정하지 않은 공고 |   |
| prtcptLmtRgnNm | 참가제한지역명 | 100 | 0 | 전국 | 검색하고자하는 참가제한지역명<br>※ 참가제한지역명 일부 입력시에도 조회 가능<br>*전국 : 지역제한을 설정하지 않은 공고 |   |
| indstrytyCd | 업종코드 | 100 | 0 | 4119 | 검색하고자하는 업종코드 |   |
| indstrytyNm | 업종명 | 100 | 0 | 토목공사업 | 검색하고자하는 업종명<br>※ 업종명 일부 입력시에도 조회 가능 |   |
| presmptPrceBgn | 추정가격시작 | 25 | 0 | 77409000 | 검색하고자하는 추정가격범위시작금액이상(원화,원) |   |
| presmptPrceEnd | 추정가격종료 | 25 | 0 | 77410000 | 검색하고자하는 추정가격범위종료금액이하(원화,원) |   |
| dtilPrdctClsfcNo | 세부품명번호 | 10 | 0 | 4010209501 | 검색하고자하는 세부품명번호 |   |
| masYn | 다수공급경쟁자여부 | 1 | 0 | N | 검색하고자하는 다수공급경쟁자여부 |   |
| prcrmntReqNo | 조달요청번호 | 13 | 0 | 제2025 | 검색하고자하는 조달요청번호 |   |
| intrntnlDivCd | 국제구분코드 | 1 | 0 | 1 | 검색하고자하는 국제구분코드<br>국내:1, 국제:2 |   |
| bizno | 사업자번호 | 10 | 0 | 1408121883 | 검색하고자 하는 업체의 사업자번호 |   |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 수 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 40 | 1 | R25BK00965123 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| ntceDivCd | 공고구분코드 | 7 | 1 | 통050001 | 공고구분<br>통050001 : 조달청 또는 나라장터 자체 공고건 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 혁신육아복합센터 건립공사(기계) 관급자재(간접가열보일러) | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| prtcptCnum | 참가업체수 | 6 | 0 | 2 | 참가업체수 |
| bidwinnrNm | 최종낙찰업체명 | 200 | 1 | 주식회사 동광보일러 | 최종낙찰된 업체의 명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrBizno | 최종낙찰업체사업자등록번호 | 10 | 1 | 1408121883 | 협상이 완료 후 최종낙찰된 업체의 사업자등록번호임 |
| bidwinnrCeoNm | 최종낙찰업체대표자명 | 35 | 0 | 박정연 | 최종낙찰된 업체의 대표자명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrAdrs | 최종낙찰업체주소 | 200 | 0 | 충청남도 아산시 수장로 67-0 (배미동) | 협상이 완료 후 최종낙찰된 업체의 주소임 |
| bidwinnrTelNo | 최종낙찰업체전화번호 | 25 | 0 | 02-6258-8989 | 협상이 완료 후 최종낙찰된 업체의 연락 전화번호임<br>핸드폰번호는 “*”로 표기 |
| sucsfbidAmt | 최종낙찰금액 | 21 | 0 | 83500000 | 최종낙찰은 개찰순위 순서대로 협상등을 통해 최종 낙찰된정보를 의미하며 최종낙찰금액은 최종낙찰된 금액 (원화,원)으로 개찰완료된건에 대하여 제공 |
| sucsfbidRate | 최종낙찰률 | 18 | 0 | 97.82 | 예정가격대비 최종낙찰금액으로 최종낙찰금액/예정가격 * 100 으로 계산되며 개찰완료된 건에 대하여 제공 (%) |
| rlOpengDt | 실개찰일시 | 19 | 0 | 2025-07-23 11:00:00 | 실제 개찰일시  “YYYY-MM-DD HH:MM:SS” |
| dminsttCd | 수요기관코드 | 7 | 0 | 6280147 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 인천광역시 종합건설본부 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| rgstDt | 등록일시 | 19 | 1 | 2025-07-23 15:20:05 | 등록일시 "YYYY-MM-DD HH:MM:SS" |
| fnlSucsfDate | 최종낙찰일자 | 10 | 0 | 2025-07-23 | 최종낙찰된 일자로 개찰완료된 건에 대하여 제공 |
| fnlSucsfCorpOfcl | 최종낙찰업체담당자 | 35 | 0 | N/A | 최종낙찰된 업체의 담당자명으로 개찰완료된 건에 대하여 제공 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getScsbidListSttusThngPPSSrch?inqryDiv=1&inqryBgnDt=202507010000&inqryEndDt=202507012359&bidNtceNm=혁신육아복합센터 건립공사(기계) 관급자재(간접가열보일러)&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00965123</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><ntceDivCd>통050001</ntceDivCd><br><bidNtceNm>혁신육아복합센터 건립공사(기계) 관급자재(간접가열보일러)</bidNtceNm><br><prtcptCnum>2</prtcptCnum><br><bidwinnrNm>주식회사 동광보일러</bidwinnrNm><br><bidwinnrBizno>1408121883</bidwinnrBizno><br><bidwinnrCeoNm>박정연</bidwinnrCeoNm><br><bidwinnrAdrs>충청남도 아산시 수장로 67-0 (배미동)</bidwinnrAdrs><br><bidwinnrTelNo>02-6258-8989</bidwinnrTelNo><br><sucsfbidAmt>83500000</sucsfbidAmt><br><sucsfbidRate>97.82</sucsfbidRate><br><rlOpengDt>2025-07-23 11:00:00</rlOpengDt><br><dminsttCd>6280147</dminsttCd><br><dminsttNm>인천광역시 종합건설본부</dminsttNm><br><rgstDt>2025-07-23 15:20:05</rgstDt><br><fnlSucsfDate>2025-07-23</fnlSucsfDate><br><fnlSucsfCorpOfcl></fnlSucsfCorpOfcl><br></item><br></items><br><numOfRows>999</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

#### [나라장터 검색조건에 의한 낙찰된 목록 현황 공사조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 17 | 오퍼레이션명(국문) | 나라장터 검색조건에 의한 낙찰된 목록 현황 공사조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getScsbidListSttusCnstwkPPSSrch** |   |
|   | 오퍼레이션 설명 | 검색조건을 공고일시, 개찰일시, 입찰공고번호, 입찰공고명, 공고기관코드, 공고기관명, 수요기관코드, 수요기관명, 참조번호, 참가제한지역코드, 참가제한지역명, 업종코드, 업종명, 추정가격시작, 추정가격종료, 세부품명번호, 다수공급경쟁자여부, 조달요청번호, 국제구분코드로 공사에대한 나라장터 최종낙찰자 목록(입찰공고번호, 입찰공고명, 참가업체수, 최종낙찰업체명, 사업자번호, 최종낙찰률, 실개찰일시, 수요기관)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1:공고게시일시, 2:개찰일시, 3:입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자 하는 조회시작일시 "YYYYMMDDHHMM"<br>조회구분이 '1'인 경우 공고게시일시 필수, '2'인 경우 개찰일시 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자 하는 조회종료일시 "YYYYMMDDHHMM"<br>조회구분이 '1'인 경우 공고게시일시 필수, '2'인 경우 개찰일시 필수 |
| bidNtceNo | 입찰공고번호 | 40 | 0 | R25BK00922727 | 검색하고자하는 입찰공고번호<br>조회구분이 '3'인 경우 필수 |
| bidNtceNm | 입찰공고명 | 1000 | 0 | (입찰대행)신활력플러스 군지정형 어르신영농단 지원사업 | 검색하고자하는 공고명<br>※ 공고명 일부 입력시에도 조회 가능 |
| ntceInsttCd | 공고기관코드 | 7 | 0 | 4791000 | 검색하고자하는 공고기관코드 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 전북특별자치도 부안군 | 검색하고자하는 공고기관명<br>※ 공고기관명 일부 입력시에도 조회 가능 |
| dminsttCd | 수요기관코드 | 7 | 0 | 4791000 | 검색하고자하는 수요기관코드<br>행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드 입력<br>행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드 입력 |
| dminsttNm | 수요기관명 | 200 | 0 | 전북특별자치도 부안군 | 검색하고자하는 수요기관명<br>※ 수요기관명 일부 입력시에도 조회 가능 |
| refNo | 참조번호 | 105 | 0 | 부안군 공고 제2025-1121호 | 검색하고자하는 참조번호 |
| prtcptLmtRgnCd | 참가제한지역코드 | 2 | 0 | 11 | 검색하고자하는 참가제한지역코드<br>11 : 서울특별시<br>26 : 부산광역시<br>27 : 대구광역시<br>28 : 인천광역시<br>29 : 광주광역시<br>30 : 대전광역시<br>31 : 울산광역시<br>36 : 세종특별자치시<br>41 : 경기도<br>42 : 강원도<br>43 : 충청북도<br>44 : 충청남도<br>45 : 전라북도<br>46 : 전라남도<br>47 : 경상북도<br>48 : 경상남도<br>50 : 제주도<br>51    : 강원특별자치도<br>52    : 전북특별자치도<br>99 : 기타<br>00: 전국<br>*전국 : 지역제한을 설정하지 않은 공고 |
| prtcptLmtRgnNm | 참가제한지역명 | 100 | 0 | 서울특별시 | 검색하고자하는 참가제한지역명<br>※ 참가제한지역명 일부 입력시에도 조회 가능<br>*전국 : 지역제한을 설정하지 않은 공고 |
| indstrytyCd | 업종코드 | 100 | 0 | 4991 | 검색하고자하는 업종코드 |
| indstrytyNm | 업종명 | 100 | 0 | 금속창호ㆍ지붕건축물조립공사업 | 검색하고자하는 업종명<br>※ 업종명 일부 입력시에도 조회 가능 |
| presmptPrceBgn | 추정가격시작 | 25 | 0 | 59090900 | 검색하고자하는 추정가격범위시작금액이상(원화,원) |
| presmptPrceEnd | 추정가격종료 | 25 | 0 | 59091000 | 검색하고자하는 추정가격범위종료금액이하(원화,원) |
| dtilPrdctClsfcNo | 세부품명번호 | 10 | 0 | 1012159801 | 검색하고자하는 세부품명번호 |
| masYn | 다수공급경쟁자여부 | 1 | 0 | N | 검색하고자하는 다수공급경쟁자여부 |
| prcrmntReqNo | 조달요청번호 | 13 | 0 | 부안군 공고 제2025-1121호 | 검색하고자하는 조달요청번호 |
| intrntnlDivCd | 국제구분코드 | 1 | 0 | 1 | 검색하고자하는 국제구분코드<br>국내:1, 국제:2 |
| bizno | 사업자번호 | 10 | 0 | 4188124255 | 검색하고자 하는 업체의 사업자번호 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 수 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 40 | 1 | R25BK00922727 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 0 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| ntceDivCd | 공고구분코드 | 7 | 1 | 통050001 | 공고구분<br>통050001 : 조달청 또는 나라장터 자체 공고건 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | (입찰대행)신활력플러스 군지정형 어르신영농단 지원사업 | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| prtcptCnum | 참가업체수 | 6 | 0 | 15 | 참가업체수 |
| bidwinnrNm | 최종낙찰업체명 | 200 | 1 | 유한회사대가건설 | 최종낙찰된 업체의 명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrBizno | 최종낙찰업체사업자등록번호 | 10 | 1 | 4188124255 | 협상이 완료 후 최종낙찰된 업체의 사업자등록번호임 |
| bidwinnrCeoNm | 최종낙찰업체대표자명 | 35 | 0 | 강훈희 | 최종낙찰된 업체의 대표자명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrAdrs | 최종낙찰업체주소 | 200 | 0 | 전북특별자치도 부안군 부안읍 서외리 455-3,제1층 제3호 | 협상이 완료 후 최종낙찰된 업체의 주소임 |
| bidwinnrTelNo | 최종낙찰업체전화번호 | 25 | 0 | 063-581-8121 | 협상이 완료 후 최종낙찰된 업체의 연락 전화번호임<br>핸드폰번호는 “*”로 표기 |
| sucsfbidAmt | 최종낙찰금액 | 21 | 0 | 58708988 | 최종낙찰은 개찰순위 순서대로 협상등을 통해 최종 낙찰된정보를 의미하며 최종낙찰금액은 최종낙찰된 금액 (원화,원)으로 개찰완료된건에 대하여 제공 |
| sucsfbidRate | 최종낙찰률 | 18 | 0 | 90.278 | 예정가격대비 최종낙찰금액으로 최종낙찰금액/예정가격 * 100 으로 계산되며 개찰완료된 건에 대하여 제공 (%) |
| rlOpengDt | 실개찰일시 | 19 | 0 | 2025-06-27 12:00:00 | 실제 개찰일시  “YYYY-MM-DD HH:MM:SS” |
| dminsttCd | 수요기관코드 | 7 | 0 | 4791000 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 전북특별자치도 부안군 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| rgstDt | 등록일시 | 19 | 1 | 2025-07-01 13:54:43 | 등록일시 "YYYY-MM-DD HH:MM:SS" |
| fnlSucsfDate | 최종낙찰일자 | 10 | 0 | 2025-07-01 | **최종낙찰된 일자로 개찰완료된 건에 대하여 제공** |
| fnlSucsfCorpOfcl | 최종낙찰업체담당자 | 35 | 0 | N/A | **최종낙찰된 업체의 담당자명으로 개찰완료된 건에 대하여 제공** |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/ getScsbidListSttusCnstwkPPSSrch?inqryDiv=1&inqryBgnDt=202507010000&inqryEndDt=202507012359&bidNtceNm=(입찰대행)신활력플러스 군지정형 어르신영농단 지원사업&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00922727</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><ntceDivCd>통050001</ntceDivCd><br><bidNtceNm>(입찰대행)신활력플러스 군지정형 어르신영농단 지원사업</bidNtceNm><br><prtcptCnum>15</prtcptCnum><br><bidwinnrNm>유한회사대가건설</bidwinnrNm><br><bidwinnrBizno>4188124255</bidwinnrBizno><br><bidwinnrCeoNm>강훈희</bidwinnrCeoNm><br><bidwinnrAdrs>전북특별자치도 부안군 부안읍 서외리 455-3,제1층 제3호</bidwinnrAdrs><br><bidwinnrTelNo>063-581-8121</bidwinnrTelNo><br><sucsfbidAmt>58708988</sucsfbidAmt><br><sucsfbidRate>90.278</sucsfbidRate><br><rlOpengDt>2025-06-27 12:00:00</rlOpengDt><br><dminsttCd>4791000</dminsttCd><br><dminsttNm>전북특별자치도 부안군</dminsttNm><br><rgstDt>2025-07-01 13:54:43</rgstDt><br><fnlSucsfDate>2025-07-01</fnlSucsfDate><br><fnlSucsfCorpOfcl></fnlSucsfCorpOfcl><br></item><br></items><br><numOfRows>999</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

#### [나라장터 검색조건에 의한 낙찰된 목록 현황 용역조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 18 | 오퍼레이션명(국문) | 나라장터 검색조건에 의한 낙찰된 목록 현황 용역조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getScsbidListSttusServcPPSSrch** |   |
|   | 오퍼레이션 설명 | 검색조건을 공고일시, 개찰일시, 입찰공고번호, 입찰공고명, 공고기관코드, 공고기관명, 수요기관코드, 수요기관명, 참조번호, 참가제한지역코드, 참가제한지역명, 업종코드, 업종명, 추정가격시작, 추정가격종료, 세부품명번호, 다수공급경쟁자여부, 조달요청번호, 국제구분코드로 용역에 대한 나라장터 최종낙찰자 목록(입찰공고번호, 입찰공고명, 참가업체수, 최종낙찰업체명, 사업자번호, 최종낙찰률, 실개찰일시, 수요기관)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1:공고게시일시, 2:개찰일시, 3:입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자 하는 조회시작일시 "YYYYMMDDHHMM"<br>조회구분이 '1'인 경우 공고게시일시 필수, '2'인 경우 개찰일시 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자 하는 조회종료일시 "YYYYMMDDHHMM"<br>조회구분이 '1'인 경우 공고게시일시 필수, '2'인 경우 개찰일시 필수 |
| bidNtceNo | 입찰공고번호 | 40 | 0 | R25BK00927163 | 검색하고자하는 입찰공고번호<br>조회구분이 '3'인 경우 필수 |
| bidNtceNm | 입찰공고명 | 1000 | 0 | 동물원(해양관, 남미관) 종합안내판 변경 제작 시행 | 검색하고자하는 공고명<br>※ 공고명 일부 입력시에도 조회 가능 |
| ntceInsttCd | 공고기관코드 | 7 | 0 | 6112581 | 검색하고자하는 공고기관코드 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 서울특별시 서울대공원 | 검색하고자하는 공고기관명<br>※ 공고기관명 일부 입력시에도 조회 가능 |
| dminsttCd | 수요기관코드 | 7 | 0 | 6112581 | 검색하고자하는 수요기관코드<br>행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드 입력<br>행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드 입력 |
| dminsttNm | 수요기관명 | 200 | 0 | 서울특별시 서울대공원 | 검색하고자하는 수요기관명<br>※ 수요기관명 일부 입력시에도 조회 가능 |
| refNo | 참조번호 | 105 | 0 | 전략기획실-4945 | 검색하고자하는 참조번호 |
| prtcptLmtRgnCd | 참가제한지역코드 | 2 | 0 | 11 | 검색하고자하는 참가제한지역코드<br>11 : 서울특별시<br>26 : 부산광역시<br>27 : 대구광역시<br>28 : 인천광역시<br>29 : 광주광역시<br>30 : 대전광역시<br>31 : 울산광역시<br>36 : 세종특별자치시<br>41 : 경기도<br>42 : 강원도<br>43 : 충청북도<br>44 : 충청남도<br>45 : 전라북도<br>46 : 전라남도<br>47 : 경상북도<br>48 : 경상남도<br>50 : 제주도<br>51    : 강원특별자치도<br>52    : 전북특별자치도<br>99 : 기타<br>00: 전국<br>*전국 : 지역제한을 설정하지 않은 공고 |
| prtcptLmtRgnNm | 참가제한지역명 | 100 | 0 | 서울특별시 | 검색하고자하는 참가제한지역명<br>※ 참가제한지역명 일부 입력시에도 조회 가능<br>*전국 : 지역제한을 설정하지 않은 공고 |
| indstrytyCd | 업종코드 | 100 | 0 | 4119 | 검색하고자하는 업종코드 |
| indstrytyNm | 업종명 | 100 | 0 | 토목공사업 | 검색하고자하는 업종명<br>※ 업종명 일부 입력시에도 조회 가능 |
| presmptPrceBgn | 추정가격시작 | 25 | 0 | 37150000 | 검색하고자하는 추정가격범위시작금액이상(원화,원) |
| presmptPrceEnd | 추정가격종료 | 25 | 0 | 37170000 | 검색하고자하는 추정가격범위종료금액이하(원화,원) |
| dtilPrdctClsfcNo | 세부품명번호 | 10 | 0 | 1012159801 | 검색하고자하는 세부품명번호 |
| masYn | 다수공급경쟁자여부 | 1 | 0 | N | 검색하고자하는 다수공급경쟁자여부 |
| prcrmntReqNo | 조달요청번호 | 13 | 0 | 800 | 검색하고자하는 조달요청번호 |
| intrntnlDivCd | 국제구분코드 | 1 | 0 | 1 | 검색하고자하는 국제구분코드<br>국내:1, 국제:2 |
| bizno | 사업자번호 | 10 | 0 | 1238640842 | 검색하고자 하는 업체의 사업자번호 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 수 |
| totalCount | 데이터 총 개수 | 4 | 1 | 10 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 40 | 1 | R25BK00927163 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 0 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| ntceDivCd | 공고구분코드 | 7 | 1 | 통050001 | 공고구분<br>통050001 : 조달청 또는 나라장터 자체 공고건 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 동물원(해양관, 남미관) 종합안내판 변경 제작 시행 | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| prtcptCnum | 참가업체수 | 6 | 0 | 1 | 참가업체수 |
| bidwinnrNm | 최종낙찰업체명 | 200 | 1 | 주식회사 나무조각 에코사인 | 최종낙찰된 업체의 명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrBizno | 최종낙찰업체사업자등록번호 | 10 | 1 | 1238640842 | 협상이 완료 후 최종낙찰된 업체의 사업자등록번호임 |
| bidwinnrCeoNm | 최종낙찰업체대표자명 | 35 | 0 | 조선미 | 최종낙찰된 업체의 대표자명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrAdrs | 최종낙찰업체주소 | 200 | 0 | 경기도 화성시 기안말길 17-0 (기안동) | 협상이 완료 후 최종낙찰된 업체의 주소임 |
| bidwinnrTelNo | 최종낙찰업체전화번호 | 25 | 0 | 070-8273-0625 | 협상이 완료 후 최종낙찰된 업체의 연락 전화번호임<br>핸드폰번호는 “*”로 표기 |
| sucsfbidAmt | 최종낙찰금액 | 21 | 0 | 38832000 | 최종낙찰은 개찰순위 순서대로 협상등을 통해 최종 낙찰된정보를 의미하며 최종낙찰금액은 최종낙찰된 금액 (원화,원)으로 개찰완료된건에 대하여 제공 |
| sucsfbidRate | 최종낙찰률 | 18 | 0 | 94.999 | 예정가격대비 최종낙찰금액으로 최종낙찰금액/예정가격 * 100 으로 계산되며 개찰완료된 건에 대하여 제공 (%) |
| rlOpengDt | 실개찰일시 | 19 | 0 | 2025-06-30 18:00:00 | 실제 개찰일시  “YYYY-MM-DD HH:MM:SS” |
| dminsttCd | 수요기관코드 | 7 | 0 | 6112581 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 서울특별시 서울대공원 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| rgstDt | 등록일시 | 19 | 1 | 2025-07-01 13:39:16 | 등록일시 "YYYY-MM-DD HH:MM:SS" |
| fnlSucsfDate | 최종낙찰일자 | 10 | 0 | 2025-07-01 | **최종낙찰된 일자로 개찰완료된 건에 대하여 제공** |
| fnlSucsfCorpOfcl | 최종낙찰업체담당자 | 35 | 0 | N/A | **최종낙찰된 업체의 담당자명으로 개찰완료된 건에 대하여 제공** |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/getScsbidListSttusServcPPSSrch?inqryDiv=1&inqryBgnDt=202507010000&inqryEndDt=202507012359&bidNtceNm 동물원(해양관, 남미관) 종합안내판 변경 제작 시행&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00927163</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><ntceDivCd>통050001</ntceDivCd><br><bidNtceNm>동물원(해양관, 남미관) 종합안내판 변경 제작 시행</bidNtceNm><br><prtcptCnum>1</prtcptCnum><br><bidwinnrNm>주식회사 나무조각 에코사인</bidwinnrNm><br><bidwinnrBizno>1238640842</bidwinnrBizno><br><bidwinnrCeoNm>조선미</bidwinnrCeoNm><br><bidwinnrAdrs>경기도 화성시 기안말길 17-0 (기안동)</bidwinnrAdrs><br><bidwinnrTelNo>070-8273-0625</bidwinnrTelNo><br><sucsfbidAmt>38832000</sucsfbidAmt><br><sucsfbidRate>94.999</sucsfbidRate><br><rlOpengDt>2025-06-30 18:00:00</rlOpengDt><br><dminsttCd>6112581</dminsttCd><br><dminsttNm>서울특별시 서울대공원</dminsttNm><br><rgstDt>2025-07-01 13:39:16</rgstDt><br><fnlSucsfDate>2025-07-01</fnlSucsfDate><br><fnlSucsfCorpOfcl></fnlSucsfCorpOfcl><br></item><br></items><br><numOfRows>10</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

#### [나라장터 검색조건에 의한 낙찰된 목록 현황 외자조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 19 | 오퍼레이션명(국문) | 나라장터 검색조건에 의한 낙찰된 목록 현황 외자조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getScsbidListSttusFrgcptPPSSrch** |   |
|   | 오퍼레이션 설명 | 검색조건을 공고일시, 개찰일시, 입찰공고번호, 입찰공고명, 공고기관코드, 공고기관명, 수요기관코드, 수요기관명, 참조번호, 참가제한지역코드, 참가제한지역명, 업종코드, 업종명, 추정가격시작, 추정가격종료, 세부품명번호, 다수공급경쟁자여부, 조달요청번호, 국제구분코드로 외자에 대한 나라장터 최종낙찰자 목록(입찰공고번호, 입찰공고명, 참가업체수, 최종낙찰업체명, 사업자번호, 최종낙찰률, 실개찰일시, 수요기관)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1:공고게시일시, 2:개찰일시, 3:입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자 하는 조회시작일시 "YYYYMMDDHHMM"<br>조회구분이 '1'인 경우 공고게시일시 필수, '2'인 경우 개찰일시 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507102359 | 검색하고자 하는 조회종료일시 "YYYYMMDDHHMM"<br>조회구분이 '1'인 경우 공고게시일시 필수, '2'인 경우 개찰일시 필수 |
| bidNtceNo | 입찰공고번호 | 40 | 0 | R25BK00857114 | 검색하고자하는 입찰공고번호<br>조회구분이 '3'인 경우 필수 |
| bidNtceNm | 입찰공고명 | 1000 | 0 | 가스크로마토그래프-질량분석기 | 검색하고자하는 공고명<br>※ 공고명 일부 입력시에도 조회 가능 |
| ntceInsttCd | 공고기관코드 | 7 | 0 | 1482021 | 검색하고자하는 공고기관코드 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 환경부 국립환경과학원 | 검색하고자하는 공고기관명<br>※ 공고기관명 일부 입력시에도 조회 가능 |
| dminsttCd | 수요기관코드 | 7 | 0 | 1482021 | 검색하고자하는 수요기관코드<br>행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드 입력<br>행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드 입력 |
| dminsttNm | 수요기관명 | 200 | 0 | 환경부 국립환경과학원 | 검색하고자하는 수요기관명<br>※ 수요기관명 일부 입력시에도 조회 가능 |
| refNo | 참조번호 | 105 | 0 | R25DC00044773 | 검색하고자하는 참조번호 |
| prtcptLmtRgnCd | 참가제한지역코드 | 2 | 0 | 00 | 검색하고자하는 참가제한지역코드<br>11 : 서울특별시<br>26 : 부산광역시<br>27 : 대구광역시<br>28 : 인천광역시<br>29 : 광주광역시<br>30 : 대전광역시<br>31 : 울산광역시<br>36 : 세종특별자치시<br>41 : 경기도<br>42 : 강원도<br>43 : 충청북도<br>44 : 충청남도<br>45 : 전라북도<br>46 : 전라남도<br>47 : 경상북도<br>48 : 경상남도<br>50 : 제주도<br>51    : 강원특별자치도<br>52    : 전북특별자치도<br>99 : 기타<br>00: 전국<br>*전국 : 지역제한을 설정하지 않은 공고 |
| prtcptLmtRgnNm | 참가제한지역명 | 100 | 0 | 전국 | 검색하고자하는 참가제한지역명<br>※ 참가제한지역명 일부 입력시에도 조회 가능<br>*전국 : 지역제한을 설정하지 않은 공고 |
| indstrytyCd | 업종코드 | 100 | 0 | 4119 | 검색하고자하는 업종코드 |
| indstrytyNm | 업종명 | 100 | 0 | 토목공사업 | 검색하고자하는 업종명<br>※ 업종명 일부 입력시에도 조회 가능 |
| presmptPrceBgn | 추정가격시작 | 25 | 0 | 0 | 검색하고자하는 추정가격범위시작금액이상(원화,원) |
| presmptPrceEnd | 추정가격종료 | 25 | 0 | 0 | 검색하고자하는 추정가격범위종료금액이하(원화,원) |
| dtilPrdctClsfcNo | 세부품명번호 | 10 | 0 | 4111540401 | 검색하고자하는 세부품명번호 |
| masYn | 다수공급경쟁자여부 | 1 | 0 | N | 검색하고자하는 다수공급경쟁자여부 |
| prcrmntReqNo | 조달요청번호 | 13 | 0 | R25DC00044773 | 검색하고자하는 조달요청번호 |
| intrntnlDivCd | 국제구분코드 | 1 | 0 | 2 | 검색하고자하는 국제구분코드<br>국내:1, 국제:2 |
| bizno | 사업자번호 | 10 | 0 | 3078701124 | 검색하고자 하는 업체의 사업자번호 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 수 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 40 | 1 | R25BK00857114 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| ntceDivCd | 공고구분코드 | 7 | 1 | 통050001 | 공고구분<br>통050001 : 조달청 또는 나라장터 자체 공고건 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | (외자)가스크로마토그래프-질량분석기 | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| prtcptCnum | 참가업체수 | 6 | 0 | 1 | 참가업체수 |
| bidwinnrNm | 최종낙찰업체명 | 200 | 1 | 주식회사 시마즈 사이언티픽 코리아 | 최종낙찰된 업체의 명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrBizno | 최종낙찰업체사업자등록번호 | 10 | 1 | 3078701124 | 협상이 완료 후 최종낙찰된 업체의 사업자등록번호임 |
| bidwinnrCeoNm | 최종낙찰업체대표자명 | 35 | 0 | 야마다 타케시 | 최종낙찰된 업체의 대표자명으로 개찰완료된 건에 대하여 제공 |
| bidwinnrAdrs | 최종낙찰업체주소 | 200 | 0 | 서울특별시 강남구 언주로 609, 9층(논현동 , 팍스타워) | 협상이 완료 후 최종낙찰된 업체의 주소임 |
| bidwinnrTelNo | 최종낙찰업체전화번호 | 25 | 0 | 042-864-1161 | 협상이 완료 후 최종낙찰된 업체의 연락 전화번호임<br>핸드폰번호는 “*”로 표기 |
| sucsfbidAmt | 최종낙찰금액 | 21 | 0 | 27538049 | 최종낙찰은 개찰순위 순서대로 협상등을 통해 최종 낙찰된정보를 의미하며 최종낙찰금액은 최종낙찰된 금액 (원화,원)으로 개찰완료된건에 대하여 제공 |
| sucsfbidRate | 최종낙찰률 | 18 | 0 | 0 | 예정가격대비 최종낙찰금액으로 최종낙찰금액/예정가격 * 100 으로 계산되며 개찰완료된 건에 대하여 제공 (%) |
| rlOpengDt | 실개찰일시 | 19 | 0 | 2025-06-05 15:00:00 | 실제 개찰일시  “YYYY-MM-DD HH:MM:SS” |
| dminsttCd | 수요기관코드 | 7 | 0 | 1482021 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 환경부 국립환경과학원 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| rgstDt | 등록일시 | 19 | 1 | 2025-07-07 09:17:48 | 등록일시 "YYYY-MM-DD HH:MM:SS" |
| FnlSucsfDate | 최종낙찰일자 | 10 | 0 | 2025-07-07 | **최종낙찰된 일자로 개찰완료된 건에 대하여 제공** |
| fnlSucsfCorpOfcl | 최종낙찰업체담당자 | 35 | 0 | N/A | **최종낙찰된 업체의 담당자명으로 개찰완료된 건에 대하여 제공** |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/ScsbidInfoService/getScsbidListSttusFrgcptPPSSrch?inqryDiv=1&inqryBgnDt=202507010000&inqryEndDt=202507012359&bidNtceNm=(외자)가스크로마토그래프-질량분석기 &pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00857114</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><ntceDivCd>통050001</ntceDivCd><br><bidNtceNm>(외자)가스크로마토그래프-질량분석기</bidNtceNm><br><prtcptCnum>1</prtcptCnum><br><bidwinnrNm>주식회사 시마즈 사이언티픽 코리아</bidwinnrNm><br><bidwinnrBizno>3078701124</bidwinnrBizno><br><bidwinnrCeoNm>야마다 타케시</bidwinnrCeoNm><br><bidwinnrAdrs>서울특별시 강남구 언주로 609, 9층(논현동 , 팍스타워)</bidwinnrAdrs><br><bidwinnrTelNo>042-864-1161</bidwinnrTelNo><br><sucsfbidAmt>27538049</sucsfbidAmt><br><sucsfbidRate></sucsfbidRate><br><rlOpengDt>2025-06-05 15:00:00</rlOpengDt><br><dminsttCd>1482021</dminsttCd><br><dminsttNm>환경부 국립환경과학원</dminsttNm><br><rgstDt>2025-07-07 09:17:48</rgstDt><br><fnlSucsfDate>2025-07-07</fnlSucsfDate><br><fnlSucsfCorpOfcl></fnlSucsfCorpOfcl><br></item><br></items><br><numOfRows>999</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

#### [나라장터 검색조건에 의한 개찰결과 물품 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 20 | 오퍼레이션명(국문) | 나라장터 검색조건에 의한 개찰결과 물품 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoThngPPSSrch** |   |
|   | 오퍼레이션 설명 | 유찰, 개찰완료, 재입찰건에 대한 개찰결과를 제공하며 검색조건을 공고일시, 개찰일시, 입찰공고번호, 입찰공고명, 공고기관코드, 공고기관명, 수요기관코드, 수요기관명, 참조번호, 참가제한지역코드, 참가제한지역명, 업종코드, 업종명, 추정가격시작, 추정가격종료, 세부품명번호, 다수공급경쟁자여부, 조달요청번호, 국제구분코드로 하여 물품에 대한 나라장터 개찰결과 목록(입찰공고번호, 입찰공고명, 개찰일시, 참가업체수, 개찰업체정보, 진행구분코드명, 입력일시, 예비가격파일존재여부, 공고기관명, 수요기관명)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1..공고일시, 2.개찰일시, 3.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 11 | 0 | R25BK00840922 | 검색하고자하는 입찰공고번호<br>조회구분이 '3'인 경우 필수 |
| bidNtceNm | 입찰공고명 | 1000 | 0 | 근접전자기장 내성 시험 시스템 구축 | 검색하고자하는 공고명<br>※ 공고명 일부 입력시에도 조회 가능 |
| ntceInsttCd | 공고기관코드 | 7 | 0 | 1230137 | 검색하고자하는 공고기관코드 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 조달청 대구지방조달청 | 검색하고자하는 공고기관명<br>※ 공고기관명 일부 입력시에도 조회 가능 |
| dminsttCd | 수요기관코드 | 7 | 0 | Z021943 | 검색하고자하는 수요기관코드<br>행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드 입력<br>행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드 입력 |
| dminsttNm | 수요기관명 | 200 | 0 | 대구경북첨단의료산업진흥재단 | 검색하고자하는 수요기관명<br>※ 수요기관명 일부 입력시에도 조회 가능 |
| refNo | 참조번호 | 105 | 0 | 곡성군 공고 2019- 1955호 | 검색하고자하는 참조번호 |
| prtcptLmtRgnCd | 참가제한지역코드 | 2 | 0 | 11 | 검색하고자하는 참가제한지역코드<br>11 : 서울특별시<br>26 : 부산광역시<br>27 : 대구광역시<br>28 : 인천광역시<br>29 : 광주광역시<br>30 : 대전광역시<br>31 : 울산광역시<br>36 : 세종특별자치시<br>41 : 경기도<br>42 : 강원도<br>43 : 충청북도<br>44 : 충청남도<br>45 : 전라북도<br>46 : 전라남도<br>47 : 경상북도<br>48 : 경상남도<br>50 : 제주도<br>51    : 강원특별자치도<br>52    : 전북특별자치도<br>99 : 기타<br>00: 전국<br>*전국 : 지역제한을 설정하지 않은 공고 |
| prtcptLmtRgnNm | 참가제한지역명 | 100 | 0 | 서울특별시 | 검색하고자하는 참가제한지역명<br>※ 참가제한지역명 일부 입력시에도 조회 가능<br>*전국 : 지역제한을 설정하지 않은 공고 |
| indstrytyCd | 업종코드 | 100 | 0 | 4119 | 검색하고자하는 업종코드 |
| indstrytyNm | 업종명 | 100 | 0 | 토목공사업 | 검색하고자하는 업종명<br>※ 업종명 일부 입력시에도 조회 가능 |
| presmptPrceBgn | 추정가격시작 | 25 | 0 | 171750000 | 검색하고자하는 추정가격범위시작금액이상(원화,원) |
| presmptPrceEnd | 추정가격종료 | 25 | 0 | 171770000 | 검색하고자하는 추정가격범위종료금액이하(원화,원) |
| dtilPrdctClsfcNo | 세부품명번호 | 10 | 0 | 1112170101 | 검색하고자하는 세부품명번호 |
| masYn | 다수공급경쟁자여부 | 1 | 0 | N | 검색하고자하는 다수공급경쟁자여부 |
| prcrmntReqNo | 조달요청번호 | 13 | 0 | R25DC00058294 | 검색하고자하는 조달요청번호 |
| intrntnlDivCd | 국제구분코드 | 1 | 0 | 1 | 검색하고자하는 국제구분코드<br>국내:1, 국제:2 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00840922 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 근접전자기장 내성 시험 시스템 구축 | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| opengDt | 개찰일시 | 19 | 1 | 2025-06-17 11:00:00 | 조달업체가 제출한 입찰서를 개찰하는 일시  “YYYY-MM-DD HH:MM:SS” |
| prtcptCnum | 참가업체수 | 6 | 0 | 2 | 참가업체수 |
| opengCorpInfo | 개찰업체정보 | 500 | 1 | 이엠테스트코리아 주식회사^1428139282^김종인^178750000^97.992 | 개찰업체정보<br>다수 낙찰자의 경우 ”낙찰예정자 다수”와 개찰순위 1위의 투찰금액과 투찰율<br>을 보여줌<br>단일 낙찰자 의 경우 업체명과 사업자번호, 대표자명, 투찰금액, 투찰율을 보여줌<br>단, 협상에 의한 계약일 경우는 투찰금액,투찰율 안나옴 |
| progrsDivCdNm | 진행구분코드명 | 4 | 1 | 개찰완료 | 진행구분이<br>유찰, 개찰완료, 재입찰로 구분 됨 |
| inptDt | 입력일시 | 19 | 0 | 2025-07-14 09:57:49 | 입력일시 “YYYY-MM-DD HH:MM:SS” |
| rsrvtnPrceFileExistnceYn | 예비가격파일존재여부 | 1 | 1 | Y | 예비가격파일존재여부(Y/N) |
| ntceInsttCd | 공고기관코드 | 7 | 1 | 1230137 | 공고를 하는 기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 조달청 대구지방조달청 | 수요기관의 의뢰를 받아 공고하는 기관의 명 |
| dminsttCd | 수요기관코드 | 7 | 0 | Z021943 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 대구경북첨단의료산업진흥재단 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| opengRsltNtcCntnts | 개찰결과공지내용 | 4000 | 0 | 공지내용참고 | 입찰공고번호, 입찰공고차수, 입찰분류번호, 재입찰번호에 해당하는 공지사항 내용 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/**ScsbidInfoService**/**getOpengResultListInfoThngPPSSrch**?inqryDiv=1&inqryBgnDt=201605010000&inqryEndDt=201605052359&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>20160505843</bidNtceNo><br><bidNtceOrd>00</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>0</rbidNo><br><bidNtceNm>중앙제어실 GATEWAY 구매설치</bidNtceNm><br><opengDt>2016-05-17 10:00:00</opengDt><br><prtcptCnum>5</prtcptCnum><br><opengCorpInfo>(주)디스엔지니어링^2208619067^남병단^11769000^89.842</opengCorpInfo><br><progrsDivCdNm>개찰완료</progrsDivCdNm><br><inptDt>2016-05-17 10:05:09</inptDt><br><rsrvtnPrceFileExistnceYn>Y</rsrvtnPrceFileExistnceYn><br><ntceInsttCd>6110136</ntceInsttCd><br><ntceInsttNm>서울특별시 상수도사업본부 강동수도사업소</ntceInsttNm><br><dminsttCd>6110136</dminsttCd><br><dminsttNm>서울특별시 상수도사업본부 강동수도사업소</dminsttNm><br><opengRsltNtcCntnts / ><br></item><br><item><br><bidNtceNo>20160503769</bidNtceNo><br><bidNtceOrd>00</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>0</rbidNo><br><bidNtceNm>광학(RapidEye) 위성영상 조달 구매</bidNtceNm><br><opengDt>2016-05-10 16:00:00</opengDt><br><prtcptCnum>1</prtcptCnum><br><opengCorpInfo>주식회사 지오포커스^1358600090^윤병현^133300000^99.925</opengCorpInfo><br><progrsDivCdNm>개찰완료</progrsDivCdNm><br><inptDt>2016-05-10 17:09:10</inptDt><br><rsrvtnPrceFileExistnceYn>Y</rsrvtnPrceFileExistnceYn><br><ntceInsttCd>1230152</ntceInsttCd><br><ntceInsttNm>조달청 전북지방조달청</ntceInsttNm><br><dminsttCd>1390802</dminsttCd><br><dminsttNm>농촌진흥청 국립농업과학원</dminsttNm><br><opengRsltNtcCntnts / ><br></item><br><item><br><bidNtceNo>20160505826</bidNtceNo><br><bidNtceOrd>00</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>0</rbidNo><br><bidNtceNm>연소시험용 점화추진제 구매</bidNtceNm><br><opengDt>2016-05-09 16:00:00</opengDt><br><prtcptCnum>0</prtcptCnum><br><opengCorpInfo /><br><progrsDivCdNm>유찰</progrsDivCdNm><br><inptDt>2016-05-10 14:53:58</inptDt><br><rsrvtnPrceFileExistnceYn>N</rsrvtnPrceFileExistnceYn><br><ntceInsttCd>Z004843</ntceInsttCd><br><ntceInsttNm>한국항공우주연구원</ntceInsttNm><br><dminsttCd>Z004843</dminsttCd><br><dminsttNm>한국항공우주연구원</dminsttNm><br><opengRsltNtcCntnts>본 건은 최종낙찰자가 없습니다. 사유 : 적격자없음</opengRsltNtcCntnts><br></item><br></items><br><numOfRows>10</numOfRows><br><pageNo>1</pageNo><br><totalCount>1684</totalCount><br></body><br></response> |

#### [나라장터 검색조건에 의한 개찰결과 공사 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 21 | 오퍼레이션명(국문) | 나라장터 검색조건에 의한 개찰결과 공사 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoCnstwkPPSSrch** |   |
|   | 오퍼레이션 설명 | 유찰, 개찰완료, 재입찰건에 대한 개찰결과를 제공하며 검색조건을 공고일시, 개찰일시, 입찰공고번호, 입찰공고명, 공고기관코드, 공고기관명, 수요기관코드, 수요기관명, 참조번호, 참가제한지역코드, 참가제한지역명, 업종코드, 업종명, 추정가격시작, 추정가격종료, 세부품명번호, 다수공급경쟁자여부, 조달요청번호, 국제구분코드로 하여 공사에 대한 나라장터 개찰결과 목록(입찰공고번호, 입찰공고명, 개찰일시, 참가업체수, 개찰업체정보, 진행구분코드명, 입력일시, 예비가격파일존재여부, 공고기관명, 수요기관명)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.공고일시,2.개찰일시,3.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 11 | 0 | R25BK00926014 | 검색하고자하는 입찰공고번호<br>조회구분이 '3'인 경우 필수 |
| bidNtceNm | 입찰공고명 | 1000 | 0 | 낭주중학교 인조 잔디 조성 및 담장 교체 공사 입찰 공고[긴급] | 검색하고자하는 공고명<br>※ 공고명 일부 입력시에도 조회 가능 |
| ntceInsttCd | 공고기관코드 | 7 | 0 | 8462058 | 검색하고자하는 공고기관코드 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 전북특별자치도교육청 전북특별자치도부안교육지원청 낭주중학교 | 검색하고자하는 공고기관명<br>※ 공고기관명 일부 입력시에도 조회 가능 |
| dminsttCd | 수요기관코드 | 7 | 0 | 8462058 | 검색하고자하는 수요기관코드<br>행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드 입력<br>행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드 입력 |
| dminsttNm | 수요기관명 | 200 | 0 | 전북특별자치도교육청 전북특별자치도부안교육지원청 낭주중학교 | 검색하고자하는 수요기관명<br>※ 수요기관명 일부 입력시에도 조회 가능 |
| refNo | 참조번호 | 105 | 0 | 전북특별자치도부안교육지원청 낭주중학교 공고 제2025 - 11호 | 검색하고자하는 참조번호 |
| prtcptLmtRgnCd | 참가제한지역코드 | 2 | 0 | 50 | 검색하고자하는 참가제한지역코드<br>11 : 서울특별시<br>26 : 부산광역시<br>27 : 대구광역시<br>28 : 인천광역시<br>29 : 광주광역시<br>30 : 대전광역시<br>31 : 울산광역시<br>36 : 세종특별자치시<br>41 : 경기도<br>42 : 강원도<br>43 : 충청북도<br>44 : 충청남도<br>45 : 전라북도<br>46 : 전라남도<br>47 : 경상북도<br>48 : 경상남도<br>50 : 제주도<br>51    : 강원특별자치도<br>52    : 전북특별자치도<br>99 : 기타<br>00: 전국<br>*전국 : 지역제한을 설정하지 않은 공고 |
| prtcptLmtRgnNm | 참가제한지역명 | 100 | 0 | 제주 | 검색하고자하는 참가제한지역명<br>※ 참가제한지역명 일부 입력시에도 조회 가능<br>*전국 : 지역제한을 설정하지 않은 공고 |
| indstrytyCd | 업종코드 | 100 | 0 | 0006 | 검색하고자하는 업종코드 |
| indstrytyNm | 업종명 | 100 | 0 | 실내건축공사업 | 검색하고자하는 업종명<br>※ 업종명 일부 입력시에도 조회 가능 |
| presmptPrceBgn | 추정가격시작 | 25 | 0 | 475700000 | 검색하고자하는 추정가격범위시작금액이상(원화,원) |
| presmptPrceEnd | 추정가격종료 | 25 | 0 | 475800000 | 검색하고자하는 추정가격범위종료금액이하(원화,원) |
| dtilPrdctClsfcNo | 세부품명번호 | 10 | 0 | 1012159801 | 검색하고자하는 세부품명번호 |
| masYn | 다수공급경쟁자여부 | 1 | 0 | Y | 검색하고자하는 다수공급경쟁자여부 |
| prcrmntReqNo | 조달요청번호 | 13 | 0 | 800 | 검색하고자하는 조달요청번호 |
| intrntnlDivCd | 국제구분코드 | 1 | 0 | 1 | 검색하고자하는 국제구분코드<br>국내:1, 국제:2 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00926014 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 0 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 낭주중학교 인조 잔디 조성 및 담장 교체 공사 입찰 공고[긴급] | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| opengDt | 개찰일시 | 19 | 1 | 2025-07-01 11:00:00 | 조달업체가 제출한 입찰서를 개찰하는 일시  “YYYY-MM-DD HH:MM:SS” |
| prtcptCnum | 참가업체수 | 6 | 0 | 374 | 참가업체수 |
| opengCorpInfo | 개찰업체정보 | 500 | 1 | 유한회사 진무건설^4028138623^이세윤^462119000^88.393 | 개찰업체정보<br>다수 낙찰자의 경우 ”낙찰예정자 다수”와 개찰순위 1위의 투찰금액과 투찰율<br>을 보여줌<br>단일 낙찰자 의 경우 업체명과 사업자번호, 대표자명, 투찰금액, 투찰율을 보여줌<br>단, 협상에 의한 계약일 경우는 투찰금액,투찰율 안나옴 |
| progrsDivCdNm | 진행구분코드명 | 4 | 1 | 개찰완료 | 진행구분이<br>유찰, 개찰완료, 재입찰로 구분 됨 |
| inptDt | 입력일시 | 19 | 0 | 2025-07-01 11:08:48 | 입력일시 “YYYY-MM-DD HH:MM:SS” |
| rsrvtnPrceFileExistnceYn | 예비가격파일존재여부 | 1 | 1 | Y | 예비가격파일존재여부(Y/N) |
| ntceInsttCd | 공고기관코드 | 7 | 1 | 8462058 | 공고를 하는 기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 전북특별자치도교육청 전북특별자치도부안교육지원청 낭주중학교 | 수요기관의 의뢰를 받아 공고하는 기관의 명 |
| dminsttCd | 수요기관코드 | 7 | 0 | 8462058 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 전북특별자치도교육청 전북특별자치도부안교육지원청 낭주중학교 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| opengRsltNtcCntnts | 개찰결과공지내용 | 4000 | 0 | 개찰완료되었습니다. | 입찰공고번호, 입찰공고차수, 입찰분류번호, 재입찰번호에 해당하는 공지사항 내용 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/**ScsbidInfoService**/**getOpengResultListInfoCnstwkPPSSrch**?inqryDiv=1&inqryBgnDt=201605010000&inqryEndDt=201605052359&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00926014</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>낭주중학교 인조 잔디 조성 및 담장 교체 공사 입찰 공고[긴급]</bidNtceNm><br><opengDt>2025-07-01 11:00:00</opengDt><br><prtcptCnum>374</prtcptCnum><br><opengCorpInfo>유한회사 진무건설^4028138623^이세윤^462119000^88.393</opengCorpInfo><br><progrsDivCdNm>개찰완료</progrsDivCdNm><br><inptDt>2025-07-01 11:08:48</inptDt><br><rsrvtnPrceFileExistnceYn>Y</rsrvtnPrceFileExistnceYn><br><ntceInsttCd>8462058</ntceInsttCd><br><ntceInsttNm>전북특별자치도교육청 전북특별자치도부안교육지원청 낭주중학교</ntceInsttNm><br><dminsttCd>8462058</dminsttCd><br><dminsttNm>전북특별자치도교육청 전북특별자치도부안교육지원청 낭주중학교</dminsttNm><br><opengRsltNtcCntnts></opengRsltNtcCntnts><br></item><br></items><br><numOfRows>999</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response |

#### [나라장터 검색조건에 의한 개찰결과 용역 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 22 | 오퍼레이션명(국문) | 나라장터 검색조건에 의한 개찰결과 용역 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoServcPPSSrch** |   |
|   | 오퍼레이션 설명 | 유찰, 개찰완료, 재입찰건에 대한 개찰결과를 제공하며 검색조건을 공고일시, 개찰일시, 입찰공고번호, 입찰공고명, 공고기관코드, 공고기관명, 수요기관코드, 수요기관명, 참조번호, 참가제한지역코드, 참가제한지역명, 업종코드, 업종명, 추정가격시작, 추정가격종료, 세부품명번호, 다수공급경쟁자여부, 조달요청번호, 국제구분코드로하여 용역에 대한 나라장터 개찰결과 목록(입찰공고번호, 입찰공고명, 개찰일시, 참가업체수, 개찰업체정보, 진행구분코드명, 입력일시, 예비가격파일존재여부, 공고기관명, 수요기관명)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.공고일시,2.개찰일시,3.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 20250701000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 11 | 0 | R25BK00882586 | 검색하고자하는 입찰공고번호<br>조회구분이 '3'인 경우 필수 |
| bidNtceNm | 입찰공고명 | 1000 | 0 | 한국생명공학연구원 지역조직 중기 발전전략 수립 | 검색하고자하는 공고명<br>※ 공고명 일부 입력시에도 조회 가능 |
| ntceInsttCd | 공고기관코드 | 7 | 0 | Z004836 | 검색하고자하는 공고기관코드 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 한국생명공학연구원 | 검색하고자하는 공고기관명<br>※ 공고기관명 일부 입력시에도 조회 가능 |
| dminsttCd | 수요기관코드 | 7 | 0 | Z004836 | 검색하고자하는 수요기관코드<br>행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드 입력<br>행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드 입력 |
| dminsttNm | 수요기관명 | 200 | 0 | 한국생명공학연구원 | 검색하고자하는 수요기관명<br>※ 수요기관명 일부 입력시에도 조회 가능 |
| refNo | 참조번호 | 105 | 0 | 제20250602-용-1호 | 검색하고자하는 참조번호 |
| prtcptLmtRgnCd | 참가제한지역코드 | 2 | 0 | 00 | 검색하고자하는 참가제한지역코드<br>11 : 서울특별시<br>26 : 부산광역시<br>27 : 대구광역시<br>28 : 인천광역시<br>29 : 광주광역시<br>30 : 대전광역시<br>31 : 울산광역시<br>36 : 세종특별자치시<br>41 : 경기도<br>42 : 강원도<br>43 : 충청북도<br>44 : 충청남도<br>45 : 전라북도<br>46 : 전라남도<br>47 : 경상북도<br>48 : 경상남도<br>50 : 제주도<br>51    : 강원특별자치도<br>52    : 전북특별자치도<br>99 : 기타<br>00: 전국<br>*전국 : 지역제한을 설정하지 않은 공고 |
| prtcptLmtRgnNm | 참가제한지역명 | 100 | 0 | 전국 | 검색하고자하는 참가제한지역명<br>※ 참가제한지역명 일부 입력시에도 조회 가능<br>*전국 : 지역제한을 설정하지 않은 공고 |
| indstrytyCd | 업종코드 | 100 | 0 | 1261 | 검색하고자하는 업종코드 |
| indstrytyNm | 업종명 | 100 | 0 | 종합여행업 | 검색하고자하는 업종명<br>※ 업종명 일부 입력시에도 조회 가능 |
| presmptPrceBgn | 추정가격시작 | 25 | 0 | 72550000 | 검색하고자하는 추정가격범위시작금액이상(원화,원) |
| presmptPrceEnd | 추정가격종료 | 25 | 0 | 72590000 | 검색하고자하는 추정가격범위종료금액이하(원화,원) |
| dtilPrdctClsfcNo | 세부품명번호 | 10 | 0 | 1012159801 | 검색하고자하는 세부품명번호 |
| masYn | 다수공급경쟁자여부 | 1 | 0 | Y | 검색하고자하는 다수공급경쟁자여부 |
| prcrmntReqNo | 조달요청번호 | 13 | 0 | 800 | 검색하고자하는 조달요청번호 |
| intrntnlDivCd | 국제구분코드 | 1 | 0 | 1 | 검색하고자하는 국제구분코드<br>국내:1, 국제:2 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00882586 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 한국생명공학연구원 지역조직 중기 발전전략 수립 | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| opengDt | 개찰일시 | 19 | 1 | 2025-06-13 11:00:00 | 조달업체가 제출한 입찰서를 개찰하는 일시  “YYYY-MM-DD HH:MM:SS” |
| prtcptCnum | 참가업체수 | 6 | 0 | 2 | 참가업체수 |
| opengCorpInfo | 개찰업체정보 | 500 | 1 | (주식회사 과학기술전략연구소^5088702880^유경만^72000000^0 | 개찰업체정보<br>다수 낙찰자의 경우 ”낙찰예정자 다수”와 개찰순위 1위의 투찰금액과 투찰율<br>을 보여줌<br>단일 낙찰자 의 경우 업체명과 사업자번호, 대표자명, 투찰금액, 투찰율을 보여줌<br>단, 협상에 의한 계약일 경우는 투찰금액,투찰율 안나옴 |
| progrsDivCdNm | 진행구분코드명 | 4 | 1 | 개찰완료 | 진행구분이<br>유찰, 개찰완료, 재입찰로 구분 됨 |
| inptDt | 입력일시 | 19 | 0 | 2025-07-01 16:52:39 | 입력일시 “YYYY-MM-DD HH:MM:SS” |
| rsrvtnPrceFileExistnceYn | 예비가격파일존재여부 | 1 | 1 | N | 예비가격파일존재여부(Y/N) |
| ntceInsttCd | 공고기관코드 | 7 | 1 | Z004836 | 공고를 하는 기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 한국생명공학연구원 | 수요기관의 의뢰를 받아 공고하는 기관의 명 |
| dminsttCd | 수요기관코드 | 7 | 0 | Z004836 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 한국생명공학연구원 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| opengRsltNtcCntnts | 개찰결과공지내용 | 4000 | 0 | 개찰결과공지내용 | 입찰공고번호, 입찰공고차수, 입찰분류번호, 재입찰번호에 해당하는 공지사항 내용 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/**ScsbidInfoService**/**getOpengResultListInfoServcPPSSrch**?inqryDiv=1&inqryBgnDt=201605010000&inqryEndDt=201605052359&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00882586</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>0</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>한국생명공학연구원 지역조직 중기 발전전략 수립</bidNtceNm><br><opengDt>2025-06-13 11:00:00</opengDt><br><prtcptCnum>2</prtcptCnum><br><opengCorpInfo>주식회사 과학기술전략연구소^5088702880^유경만^72000000^0</opengCorpInfo><br><progrsDivCdNm>개찰완료</progrsDivCdNm><br><inptDt>2025-07-01 16:52:39</inptDt><br><rsrvtnPrceFileExistnceYn>N</rsrvtnPrceFileExistnceYn><br><ntceInsttCd>Z004836</ntceInsttCd><br><ntceInsttNm>한국생명공학연구원</ntceInsttNm><br><dminsttCd>Z004836</dminsttCd><br><dminsttNm>한국생명공학연구원</dminsttNm><br><opengRsltNtcCntnts></opengRsltNtcCntnts><br></item><br></items><br><numOfRows>10</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

#### [나라장터 검색조건에 의한 개찰결과 외자 목록 조회] 오퍼레이션 명세

| 오퍼레이션 정보 | 오퍼레이션 번호 | 23 | 오퍼레이션명(국문) | 나라장터 검색조건에 의한 개찰결과 외자 목록 조회 |   |
| --- | --- | --- | --- | --- | --- |
|   | 오퍼레이션 유형 | 조회(목록) | 오퍼레이션명(영문) | **getOpengResultListInfoFrgcptPPSSrch** |   |
|   | 오퍼레이션 설명 | 유찰, 개찰완료, 재입찰건에 대한 개찰결과를 제공하며 검색조건을 공고일시, 개찰일시, 입찰공고번호, 입찰공고명, 공고기관코드, 공고기관명, 수요기관코드, 수요기관명, 참조번호, 참가제한지역코드, 참가제한지역명, 업종코드, 업종명, 추정가격시작, 추정가격종료, 세부품명번호, 다수공급경쟁자여부, 조달요청번호, 국제구분코드로 하여 외자에 대한 나라장터 개찰결과 목록(입찰공고번호, 입찰공고명, 개찰일시, 참가업체수, 개찰업체정보, 진행구분코드명, 입력일시, 예비가격파일존재여부, 공고기관명, 수요기관명)을 조회 |   |   |   |
|   | Call Back URL | N/A |   |   |   |
|   | 최대 메시지 사이즈 | [ 4000bytes] |   |   |   |
|   | 평균 응답 시간 | [     500    ms] | 초당 최대 트랜잭션 |   | [     30    tps] |

##### 요청 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| ServiceKey | 서비스키 | 400 | 1 | 공공데이터포털에서 받은 인증키 | 공공데이터포털에서 받은 인증키 |
| type | 타입 | 4 | 0 | json | 오픈API 리턴 타입을 JSON으로 받고 싶을 경우 'json' 으로 지정 |
| inqryDiv | 조회구분 | 1 | 1 | 1 | 검색하고자하는 조회구분<br>1.공고일시, 2.개찰일시, 3.입찰공고번호 |
| inqryBgnDt | 조회시작일시 | 12 | 0 | 202507010000 | 검색하고자하는 시작일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2일 경우 필수 |
| inqryEndDt | 조회종료일시 | 12 | 0 | 202507012359 | 검색하고자하는 종료일시<br>'YYYYMMDDHHMM'<br>조회구분 1,2일 경우 필수 |
| bidNtceNo | 입찰공고번호 | 11 | 0 | R25BK00916730 | 검색하고자하는 입찰공고번호<br>조회구분이 '3'인 경우 필수 |
| bidNtceNm | 입찰공고명 | 1000 | 0 | 외자조달요청(북부지원 유도결합플라즈마 질량분석기 | 검색하고자하는 공고명<br>※ 공고명 일부 입력시에도 조회 가능 |
| ntceInsttCd | 공고기관코드 | 7 | 0 | 1230000 | 검색하고자하는 공고기관코드 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 조달청 | 검색하고자하는 공고기관명<br>※ 공고기관명 일부 입력시에도 조회 가능 |
| dminsttCd | 수요기관코드 | 7 | 0 | 1230000 | 검색하고자하는 수요기관코드<br>행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드 입력<br>행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드 입력 |
| dminsttNm | 수요기관명 | 200 | 0 | 조달청 | 검색하고자하는 수요기관명<br>※ 수요기관명 일부 입력시에도 조회 가능 |
| refNo | 참조번호 | 105 | 0 | R25DC00054022 | 검색하고자하는 참조번호 |
| prtcptLmtRgnCd | 참가제한지역코드 | 2 | 0 | 00 | 검색하고자하는 참가제한지역코드<br>11 : 서울특별시<br>26 : 부산광역시<br>27 : 대구광역시<br>28 : 인천광역시<br>29 : 광주광역시<br>30 : 대전광역시<br>31 : 울산광역시<br>36 : 세종특별자치시<br>41 : 경기도<br>42 : 강원도<br>43 : 충청북도<br>44 : 충청남도<br>45 : 전라북도<br>46 : 전라남도<br>47 : 경상북도<br>48 : 경상남도<br>50 : 제주도<br>51    : 강원특별자치도<br>52    : 전북특별자치도<br>99 : 기타<br>00: 전국<br>*전국 : 지역제한을 설정하지 않은 공고 |
| prtcptLmtRgnNm | 참가제한지역명 | 100 | 0 | 전국 | 검색하고자하는 참가제한지역명<br>※ 참가제한지역명 일부 입력시에도 조회 가능<br>*전국 : 지역제한을 설정하지 않은 공고 |
| indstrytyCd | 업종코드 | 100 | 0 | 4119 | 검색하고자하는 업종코드 |
| indstrytyNm | 업종명 | 100 | 0 | 토목공사업 | 검색하고자하는 업종명<br>※ 업종명 일부 입력시에도 조회 가능 |
| presmptPrceBgn | 추정가격시작 | 25 | 0 | 0 | 검색하고자하는 추정가격범위시작금액이상(원화,원) |
| presmptPrceEnd | 추정가격종료 | 25 | 0 | 0 | 검색하고자하는 추정가격범위종료금액이하(원화,원) |
| dtilPrdctClsfcNo | 세부품명번호 | 10 | 0 | 4111540401 | 검색하고자하는 세부품명번호 |
| masYn | 다수공급경쟁자여부 | 1 | 0 | Y | 검색하고자하는 다수공급경쟁자여부 |
| prcrmntReqNo | 조달요청번호 | 13 | 0 | R25DC00054022 | 검색하고자하는 조달요청번호 |
| intrntnlDivCd | 국제구분코드 | 1 | 0 | 1 | 검색하고자하는 국제구분코드<br>국내:1, 국제:2 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 응답 메시지 명세

| 항목명(영문) | 항목명(국문) | 항목크기 | 항목구분 | 샘플데이터 | 항목설명 |
| --- | --- | --- | --- | --- | --- |
| resultCode | 결과코드 | 2 | 1 | 00 | 결과코드 |
| resultMsg | 결과메세지 | 50 | 1 | 정상. | 결과메세지 |
| numOfRows | 한 페이지 결과 수 | 4 | 1 | 10 | 한 페이지 결과 수 |
| pageNo | 페이지 번호 | 4 | 1 | 1 | 페이지 번호 |
| totalCount | 데이터 총 개수 | 4 | 1 | 17 | 데이터 총 개수 |
| bidNtceNo | 입찰공고번호 | 11 | 1 | R25BK00916730 | 입찰공고 관리번호이며 조달청나라장터 공고건의 형식은 년도(4)+월(2)+순번(5)이며 자체전자조달시스템 보유기관은 각 기관별 형식 별도 사용<br>*차세대나라장터 번호체계 개편 : R+년도(2)+단계구분(2)+순번(8) 총 13자리 구성<br>- 단계구분:<br>BK(입찰),<br>TA(계약),<br>DD:(발주계획),<br>BD(사전규격),<br>BK(통합입찰) |
| bidNtceOrd | 입찰공고차수 | 3 | 1 | 000 | 입찰공고차수는 해당 입찰공고에 대한 재공고 및 재입찰 등이 발생되었을 경우 증가되는 수 |
| bidClsfcNo | 입찰분류번호 | 5 | 1 | 1 | 동일한 입찰공고번호에 대한 집행일련번호 |
| rbidNo | 재입찰번호 | 3 | 1 | 000 | 재입찰번호 |
| bidNtceNm | 입찰공고명 | 1000 | 1 | 외자조달요청(북부지원 유도결합플라즈마 질량분석기) | 공사명 또는 사업명이라고도 하며 입찰공고 내용을 요약한 이름 |
| opengDt | 개찰일시 | 19 | 1 | 2025-07-01 13:00:00 | 조달업체가 제출한 입찰서를 개찰하는 일시  “YYYY-MM-DD HH:MM:SS” |
| prtcptCnum | 참가업체수 | 6 | 0 | 1 | 참가업체수 |
| opengCorpInfo | 개찰업체정보 | 500 | 1 | 써모피셔사이언티픽코리아 주식회사^1178146910^석수진^173500^0 | 개찰업체정보<br>다수 낙찰자의 경우 ”낙찰예정자 다수”와 개찰순위 1위의 투찰금액과 투찰율<br>을 보여줌<br>단일 낙찰자 의 경우 업체명과 사업자번호, 대표자명, 투찰금액, 투찰율을 보여줌<br>단, 협상에 의한 계약일 경우는 투찰금액,투찰율 안나옴 |
| progrsDivCdNm | 진행구분코드명 | 4 | 1 | 개찰완료 | 진행구분이<br>유찰, 개찰완료, 재입찰로 구분 됨 |
| inptDt | 입력일시 | 19 | 0 | 2025-07-01 13:10:54 | 입력일시 “YYYY-MM-DD HH:MM:SS” |
| rsrvtnPrceFileExistnceYn | 예비가격파일존재여부 | 1 | 1 | N | 예비가격파일존재여부(Y/N) |
| ntceInsttCd | 공고기관코드 | 7 | 1 | 1230000 | 공고를 하는 기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| ntceInsttNm | 공고기관명 | 200 | 0 | 조달청 | 수요기관의 의뢰를 받아 공고하는 기관의 명 |
| dminsttCd | 수요기관코드 | 7 | 0 | 6440071 | 실제 수요기관의 코드로 행자부코드(행정자치부에서 부여한 기관코드)가 있는 경우 행자부코드가 행자부코드가 없는 경우 조달청에서 부여한 수요기관 코드가 표기됨 |
| dminsttNm | 수요기관명 | 200 | 0 | 충청남도 보건환경연구원 | 중앙조달인 경우 조달사업에 관한 법률 제2조(정의)에 따라 수요물자의 구매 공급 또는 시설공사 계약의 체결을 조달청장에게 요청할 수 있도록 조달청장이 인정하여 등록한 기관 또는 자체전자조달시스템을 이용하는 기관인 경우 계약을 의뢰한 기관의 명으로 공고기관과 수요기관이 동일할 수 있음 |
| opengRsltNtcCntnts | 개찰결과공지내용 | 4000 | 0 | 개찰결과공지내용 | 입찰공고번호, 입찰공고차수, 입찰분류번호, 재입찰번호에 해당하는 공지사항 내용 |

※ 항목구분 : 필수(1), 옵션(0), 1건 이상 복수건(1..n), 0건 또는 복수건(0..n)

##### 요청 / 응답 메시지 예제

| REST(URI) |
| --- |
| http://apis.data.go.kr/1230000/as/**ScsbidInfoService**/**getOpengResultListInfoFrgcptPPSSrch**?inqryDiv=1&inqryBgnDt=201605010000&inqryEndDt=201605052359&pageNo=1&numOfRows=10&ServiceKey=인증키 |
| 응답 메시지 |
| <response><br><header><br><resultCode>00</resultCode><br><resultMsg>정상</resultMsg><br></header><br><body><br><items><br><item><br><bidNtceNo>R25BK00916730</bidNtceNo><br><bidNtceOrd>000</bidNtceOrd><br><bidClsfcNo>1</bidClsfcNo><br><rbidNo>000</rbidNo><br><bidNtceNm>외자조달요청(북부지원 유도결합플라즈마 질량분석기)</bidNtceNm><br><opengDt>2025-07-01 13:00:00</opengDt><br><prtcptCnum>1</prtcptCnum><br><opengCorpInfo>써모피셔사이언티픽코리아 주식회사^1178146910^석수진^173500^0</opengCorpInfo><br><progrsDivCdNm>개찰완료</progrsDivCdNm><br><inptDt>2025-07-01 13:10:54</inptDt><br><rsrvtnPrceFileExistnceYn>N</rsrvtnPrceFileExistnceYn><br><ntceInsttCd>1230000</ntceInsttCd><br><ntceInsttNm>조달청</ntceInsttNm><br><dminsttCd>6440071</dminsttCd><br><dminsttNm>충청남도 보건환경연구원</dminsttNm><br><opengRsltNtcCntnts></opengRsltNtcCntnts><br></item><br></items><br><numOfRows>999</numOfRows><br><pageNo>1</pageNo><br><totalCount>1</totalCount><br></body><br></response> |

<br>

- **OPEN API 에러코드별 조치방안**

| **Code** | **코드값** | **설명** | **조치방안** |
| --- | --- | --- | --- |
| 01 | Application Error | 제공기관 서비스 제공 상태가 원할하지 않습니다. | 서비스 제공기관의 관리자에게 문의하시기 바랍니다. |
| 02 | DB Error | 제공기관 서비스 제공 상태가 원할하지 않습니다. | 서비스 제공기관의 관리자에게 문의하시기 바랍니다. |
| 03 | No Data | 데이터 없음 에러 |   |
| 04 | HTTP Error | 제공기관 서비스 제공 상태가 원할하지 않습니다. | 서비스 제공기관의 관리자에게 문의하시기 바랍니다. |
| 05 | service time out | 제공기관 서비스 제공 상태가 원할하지 않습니다 | 서비스 제공기관의 관리자에게 문의하시기 바랍니다. |
| 06 | 날짜Format 에러 | 날짜 Default, Format Error | 날짜형식을 확인 하시기 바랍니다. |
| 07 | 입력범위값 초과 에러 | 요청하신 OpenAPI의 파라미터 입력값 범위가 초과 되었습니다. | 기술문서를 다시 한번 확인하여 주시기 바랍니다. |
| 08 | 필수값 입력 에러 | 요청하신 OpenAPI의 필수 파라미터가 누락되었습니다. | 기술문서를 다시 한번 확인하여 주시기 바랍니다. |
| 10 | 잘못된 요청 파라미터 에러 | OpenAPI 요청시 ServiceKey 파라미터가 없음 | -OpenAPI 요청시 ServiceKey 파라미터가 누락되었습니다.<br>-OpenAPI 요청 URL을 확인하시기 바랍니다. |
| 11 | 필수 요청 파라미터가 없음 | 요청하신 OpenAPI의 필수 파라미터가 누락되었습니다. | 기술문서를 다시 한번 확인하여 주시기 바랍니다. |
| 12 | 해당 오픈API 서비스가 없거나 폐기됨 | OpenAPI 호출시 URL이 잘못됨 | -제공기관 관리자에게 폐기된 서비스인지 확인바랍니다.<br>폐기된 서비스가 아니면 개발가이드에서 OpenAPI요청 URL을 다시 확인하시기 바랍니다. |
| 20 | 서비스 접근 거부 | 활용승인이 되지 않은 OpenAPI호출 | -OpenAPI활용신청정보의 승인상태를 확인하시기 바랍니다.<br>-활용신청에 대해 제공기관 담당자가 확인 후 '승인'이후 부터 사용할 수 있습니다.<br>-신청 후 2~3일 소요되고 결과는 회원가입 시 등록한 e-mail로 발송됩니다. |
| 22 | 서비스 요청 제한 횟수 초과 에러 | 일일 활용건수가 초과함(활용건수 증가 필요) | -OpenAPI활용신청정보의 서비스 상세기능별 일일 트래픽량을 확인하시기 바랍니다.<br>-개발계정의 경우 제공기관에서 정의한 트래픽을 초과하여 활용할 수 없습니다.<br>-운영계정의 경우 변경신청을 통해서 일일트래픽량을 변경 할 수 있습니다. |
| 30 | 등록되지 않은 서비스 키 | 잘못된 서비스키를 사용하였거나 서비스키를 URL인코딩하지 않음 | -OpenAPI활용신청정보의 발급받은 서비스키를 다시 확인하시기 바랍니다.<br>- 서비스키 값이 같다면 서비스키가 URL 인코등 되었는지 다시 확인하시기 바랍니다. |
| 31 | 기한 만료된 서비스 키 | OpenAPI 사용기간이 만료됨<br>(활용연장신청 후 사용가능) | -OpenAPI 활용신청정보의 활용기간을 확인합니다.<br>-활용기간이 지난 서비스는 이용할 수 없으며 연장신청을 통해 승인 받은 후 다시 이용가능 합니다. |
| 32 | 등록되지 않은 도메인명 또는 IP주소 | 활용신청한 서버의 IP와 실제 OpenAPI호출한 서버가 다를 경우 | -OpenAPI 활용신청정보의 등록된 도메인명이나 IP주소를 다시 확인합니다.<br>-IP나 도메인의 정보를 변경하기 위해 변경신청을 할 수 있습니다. |

-