Here is a **ready-to-paste serious source list** for your `sources/seed_urls.csv`.

It is designed for the **Long Sieyuan / Short Oilfield Services** thesis.

```csv
source_name,url,company,sector,document_type,theme
IEA Electricity 2026,https://www.iea.org/reports/electricity-2026,IEA,Grid Infrastructure,Industry Report,Electricity Demand
IEA Electricity 2026 - Grids,https://www.iea.org/reports/electricity-2026/grids,IEA,Grid Infrastructure,Industry Report,Grid Resilience
IEA Electricity Grids and Secure Energy Transitions,https://iea.blob.core.windows.net/assets/afebed83-db6b-4e38-8fe7-4ed4f506a742/ElectricityGridsandSecureEnergyTransitions.pdf,IEA,Grid Infrastructure,PDF Report,Grid Resilience
IEA Grid Hosting Capacity Chart,https://www.iea.org/data-and-statistics/charts/estimated-grid-hosting-capacity-that-can-be-unlocked-via-non-firm-connection-agreements-and-technology-upgrades-by-source,IEA,Grid Infrastructure,Data / Chart,Grid Resilience
Sieyuan Electric Financial Reports,https://en.sieyuan.com/report,Sieyuan Electric,Grid Infrastructure,Investor Page,Company Financials
Sieyuan Electric HKEX Draft Document,https://www1.hkexnews.hk/app/sehk/2026/108195/documents/sehk26021100491.pdf,Sieyuan Electric,Grid Infrastructure,HKEX Filing,Company Financials
Sieyuan Electric Audit Report 2025,https://en.sieyuan.com/uploads/upload/files/20250620/1be2f74797ea63b8294e095870ea931a.pdf,Sieyuan Electric,Grid Infrastructure,PDF Financial Report,Company Financials
Sieyuan Electric Investment and Cooperation,https://en.sieyuan.com/cooperation,Sieyuan Electric,Grid Infrastructure,Investor Page,Company Overview
Halliburton Investor Relations,https://ir.halliburton.com/,Halliburton,Oilfield Services,Investor Page,Company Overview
Halliburton Quarterly Results and Presentations,https://ir.halliburton.com/financial-information/quarterly-results,Halliburton,Oilfield Services,Investor Page,Company Financials
Halliburton Q1 2026 Results,https://www.halliburton.com/en/about-us/press-release/halliburton-announces-first-quarter-2026-results,Halliburton,Oilfield Services,Earnings Release,Company Financials
Halliburton Q1 2026 Earnings Transcript,https://www.fool.com/earnings/call-transcripts/2026/04/21/halliburton-hal-q1-2026-earnings-transcript/,Halliburton,Oilfield Services,Earnings Transcript,Oilfield Cost Pressure
Halliburton Q1 2026 Yahoo Earnings Call,https://finance.yahoo.com/quote/HAL/earnings/HAL-Q1-2026-earnings_call-544129.html/,Halliburton,Oilfield Services,Earnings Transcript,Oilfield Cost Pressure
Reuters Halliburton Q1 2026 Costs from Iran War,https://www.reuters.com/business/energy/halliburton-posts-higher-first-quarter-profit-2026-04-21/,Halliburton,Oilfield Services,News Article,Oilfield Cost Pressure
SLB Investor Relations,https://investorcenter.slb.com/,SLB,Oilfield Services,Investor Page,Company Overview
SLB Q1 2026 Prepared Remarks,https://investorcenter.slb.com/static-files/55302a14-51da-4f56-a671-09e64072a3ba,SLB,Oilfield Services,Earnings Remarks PDF,Oilfield Cost Pressure
SLB Q1 2026 Earnings Transcript,https://www.fool.com/earnings/call-transcripts/2026/04/24/slb-slb-q1-2026-earnings-call-transcript/,SLB,Oilfield Services,Earnings Transcript,Oilfield Cost Pressure
SLB Q1 2026 Yahoo Earnings Call,https://finance.yahoo.com/quote/SCL.F/earnings/SCL.F-Q1-2026-earnings_call-545615.html,SLB,Oilfield Services,Earnings Transcript,Oilfield Cost Pressure
Reuters SLB Q1 2026 Supply Chain Disruption,https://www.reuters.com/business/energy/oilfield-services-provider-slb-posts-lower-quarterly-profit-iran-war-hit-2026-04-24/,SLB,Oilfield Services,News Article,Oilfield Cost Pressure
Baker Hughes Investor Relations,https://investors.bakerhughes.com/,Baker Hughes,Oilfield Services,Investor Page,Company Overview
NOV Investor Relations,https://investors.nov.com/,NOV,Oilfield Services,Investor Page,Company Overview
EIA Today in Energy,https://www.eia.gov/todayinenergy/,EIA,Energy Market,Industry Page,Energy Market
EIA International Energy Outlook,https://www.eia.gov/outlooks/ieo/,EIA,Energy Market,Industry Report,Energy Demand
Data Center Dynamics,https://www.datacenterdynamics.com/en/,Data Center Infrastructure,Electricity Demand,Industry News,Electricity Demand
Power Engineering,https://www.power-eng.com/,Power Engineering,Grid Infrastructure,Industry News,Grid Resilience
Offshore Energy,https://www.offshore-energy.biz/,Offshore Energy,Oilfield Services,Industry News,Oil Logistics
```

And here is the matching `sources/rss_feeds.csv`:

```csv
source_name,feed_url,sector,theme
IEA News,https://www.iea.org/rss/news.xml,Energy,Energy Policy
EIA Today in Energy,https://www.eia.gov/rss/todayinenergy.xml,Energy,Energy Market
Offshore Energy,https://www.offshore-energy.biz/feed/,Oilfield Services,Oil Logistics
Power Engineering,https://www.power-eng.com/feed/,Grid Infrastructure,Grid Resilience
Data Center Dynamics,https://www.datacenterdynamics.com/en/rss/,Data Centers,Electricity Demand
```

Use these first because they cover the core evidence buckets:

| Bucket              | Sources                                            |
| ------------------- | -------------------------------------------------- |
| Grid demand         | IEA Electricity 2026, IEA Grids, Power Engineering |
| Long company        | Sieyuan financial reports, HKEX draft document     |
| Short company       | Halliburton / SLB transcripts and releases         |
| Oilfield disruption | Reuters, transcripts, Offshore Energy              |
| Electricity demand  | IEA, EIA, Data Center Dynamics                     |

A few of these pages may require manual download or may block automated extraction. For those, download the PDF or copy the text manually into `data/raw/text/`, then run the paragraph builder.
