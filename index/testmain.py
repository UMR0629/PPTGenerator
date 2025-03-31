from index.index import PaperSectionSummary,PaperInfo,SectionContent
from information_extrator.result_extraction import parse_output_to_section 
from information_extrator.extract_function import generate_presentation_summary,generate_with_feedback
tmp=PaperInfo(title="Leveraging Semantic Relations in Code and Data to Enhance Taint Analysis of Embedded Systems",authors="Jiaxu Zhao",date=2024)
tmp.add_outline_section("Leveraging Semantic Relations in Code and Data to Enhance Taint Analysis of Embedded Systems","Abstract")
tmp.add_content_to_leaf("Abstract","IoT devices have significantly impacted our daily lives,and detecting vulnerabilities in embedded systems early on is critical for ensuring their security. Among the existing vulnerability detection techniques for embedded systems, static taint analysis has been proven effective in detecting severevulnerabilities, such as command injection vulnerabilities,which can cause remote code execution. Nevertheless, static taint analysis is faced with the problem of identifying sources comprehensively and accurately. This paper presents LARA, a novel static taint analysis technique to detect vulnerabilities in embedded systems. The design of LARA is inspired by an observation that pertains to semantic relations within and between the code and data of embedded software: user input entries can be categorized as URIs or keys (data), and identifying their handling code(code) and relations can help systematically and comprehensively identify the sources for taint analysis. Transforming the observation into a practical methodology poses challenges.To address these challenges, LARA employs a combination of pattern-based static analysis and large language model(LLM)-aided analysis, aiming to replicate how human experts would utilize the findings during analysis and enhance it. The patternbased static analysis simulates human experience, while the LLM-aided analysis captures the way human experts perceive code semantics. We implemented LARA and evaluated it on 203 IoT devices from 21 vendors. In general, LARA detects 556 and 602 more known vulnerabilities than SATC and KARONTE while reducing false positives by 57.0% and 54.3%. Meanwhile, with more sources and sinks from LARA, EMTAINT can detect 245 more vulnerabilities. To date, LARA has found 245 0-day vulnerabilities in 57 devices, all of which were confirmed or fixed with 162 CVE IDs assigned")
tmp.add_outline_section("Leveraging Semantic Relations in Code and Data to Enhance Taint Analysis of Embedded Systems","Introduction")
tmp.add_content_to_leaf("Introduction","""The Internet of Things (IoT) has become an indispensable part of our daily lives, and the number of devices in use is expected to reach 27.1 billion by 2025 [2]. However, this growth has also resulted in an increase in vulnerabilities in embedded systems. According to recent statistics [6], weekly attacks on IoT devices have increased by 41% per organization in the first two months of 2023 compared to 2022. The threat of IoT vulnerabilities includes numerous vulnerabilities, some [4, 5, 47] of which are easily exploited and impact an average of 14% to 49% of organizations worldwide on a weekly basis. Hence, early detecting vulnerabilities in embedded systems has become crucial. IoT devices with web services are more susceptible to attacks compared to other IoT devices [10]. This is because while web services provide a convenient interface for device control and configuration, they also create opportunities for remote attacks if the underlying backend contains vulnerabilities. Thus, detecting vulnerabilities in IoT devices relying on web services is crucial. Most existing techniques [7,8,55,59] have limited effectiveness in detecting vulnerabilities in the backend programs of the web services in IoT devices. The testing techniques suffer from low code coverage and only focus on memory-related vulnerabilities. In comparison, static taint analysis is more suitable for detecting a wider variety of vulnerabilities. Taint analysis tracks and analyzes the flow of tainted information in a program, using source, sink, and taint propagation [49]. The source is where user inputs are introduced, the sink is where potentially risky operations occur, and taint propagation analysis examines how tainted markers propagate along variable dependencies in the program. Currently, most researches focus on taint propagation analysis, which employs techniques such as multi-binary tracking or pointer analysis to obtain more efficient and accurate analysis results [12,38]. However, their effectiveness on embedded systems is not significant. This is because traditional sources such as recv function are not effective in revealing the characteristics of user input entry identification and processing in embedded systems, thereby missing many potential vulnerabilities. To address the source identification challenge, a recent advancement in static taint analysis called SATC [10] proposes to leverage common input keywords between the frontend and backend to identify the user input handling code in the backend as sources. It can improve static taint analysis by providing more sources. Nevertheless, SATC misses certain sources (at least 82.5% according to our investigation) because some hidden user input handling code in the backend
does not have frontend counterparts and some non-hidden user input entries are ignored due to the incomplete rules used
for extracting the keywords. Additionally, SATC still suffers from high false positives (52.7%) for the detected sources due to a lack of awareness of dangling keywords with no/unreachable handling code. The falsely identified sources could affect the result of final vulnerability detection (missing over 87.3% with 75.2% false positives). In conclusion, static taint analysis shows promise in detecting vulnerabilities in IoT web services, but extracting sources systematically remains an open problem.
To mitigate false negatives and false positives in source identification, we conducted a comprehensive analysis of the web services in mainstream devices and made an observation relates to the characteristics of the user input entries. User inputs for the web services are typically encoded as key-value pairs organized by forms or form-like data [22]. Rather than treating all user input entries equally, separating them into URIs and keys enables better utilization of their mapping to identify corresponding backend handling codes and more sources effectively. Maintaining a mapping between them can facilitate the identification of their corresponding backend handling codes. These code of the functions, in turn, can reveal hidden URIs and keys, leading to the discovery of additional sources. However, how to identify sources based on the complex relations among URIs and keys and the corresponding pattern between them and the backend code remains a challenge. Additionally, the semantic information in the backend code can facilitate more precise pattern-based static analysis, such as inferring the purpose of a function. Effectively perform semantic-based analysis add combine it with pattern-based analysis is another challenge. In this paper, we propose LARA2, a novel static taint analysis technique for detecting vulnerabilities in embedded
systems. LARA utilizes URIs and keys extracted from the frontend to determine their corresponding handling code in the backend. This process is achieved through a combination of pattern-based static analysis and large language model (LLM)-aided analysis, aiming to replicate how human experts perform the identification based on previous experience and code semantics. The pattern-based static analysis leverages predefined rules and pattern matching, which simulates human experience, to address the first challenge. Meanwhile, the LLM-aided analysis performs the identification from the code semantics aspect to address the second challenge, as LLMs have been shown effective for summarizing the semantics
of functions [16, 25, 37]. LARA then combines the results obtained from both analyses to generate two sets of codes that
handle URIs and keys, respectively. By analyzing the URI and key handling codes, LARA can also identify the other URIs and keys that are handled by the same functions. In this manner, LARA can systematically and precisely identify the key handling functions and use them to extract sources. Regarding sinks, LARA analyzes the primary program and its related shared libraries to identify calls to dangerous operations as sinks. Finally, using the identified sources and sinks, LARA performs the static taint analysis that supports inter-process analysis to detect potential vulnerabilities. We implemented LARA as a static taint analysis framework and evaluated it on the dataset used by SATC, which includes 203 devices from 21 vendors such as DLink, Tenda, NetGear and others. The evaluation results indicate that LARA can detect significantly more vulnerabilities with fewer false positives than both SATC and KARONTE. Specifically, LARA can detect 556 and 602 more known vulnerabilities than SATC
and KARONTE, respectively, while reducing false positives by 57.0% and 54.3%. Additionally, EMTAINT could detect 245
more vulnerabilities with the assistance of LARA. To comprehensively understand the capability of each component in LARA, we also conducted an ablation study and the results showed that the pattern-based static analysis, LLM-aided analysis, and sink extraction can all improve the overall performance. Last but not least, we applied LARA to the firmware dataset for vulnerability detection. In total, we have found 245 0-day vulnerabilities in 57 devices, with all confirmed or fixed by the developers and 162 CVE IDs assigned. In summary, we make the following contributions: • We tackle the technical challenges and transform the
observation into a novel static taint analysis technique called LARA. LARA can capture sources with low false positive and false negative rates and thus is capable of detecting more vulnerabilities. • We implemented LARA and comprehensively evaluated
its performance in vulnerability detection, source identification and sink identification. The results show that LARA can significantly outperform the state-of-the-art IoT static taint analysis techniques by detecting more vulnerabilities with fewer false positives. • We discovered 245 0-day vulnerabilities in 57 devices from 13 vendors. To date, all have been confirmed or
fixed and 162 CVE IDs have been assigned. We make the raw data, detailed information and source code of LARA available on the LARA-Site: https://sites.google.com/view/lara-data.""")
tmp.add_outline_section("Leveraging Semantic Relations in Code and Data to Enhance Taint Analysis of Embedded Systems","Motivating Example")
tmp.add_outline_section("Motivating Example","2.1 Threat Model")

tmp.add_content_to_leaf("2.1 Threat Model","""In this paper, we focus on attacks against WEB services in
embedded systems. The threat model assumes that the attacker can obtain the corresponding firmware from the vendor
website and access the target over a local (LAN) or wide area
(WAN) network and send malicious HTTP requests to the
services. On the service side, the backend programs, including middleware, CGI programs, and related shared libraries,
handle these malicious data. Usually, the data in the HTTP
request has corresponding labels in the frontend, but there are
hidden data without frontend labels in the backend programs.
The vulnerability CVE-B shown in Figure 1 is caused by such
hidden data. By analyzing the backend program, attackers can
obtain these non-hidden and hidden data and then send crafted
HTTP requests that inject payloads to the vulnerable backend
handling code, leading to consequences like denial-of-service
(DoS) and remote-code-execution (RCE)""")

tmp.add_outline_section("Motivating Example","2.2 Observation")
tmp.add_content_to_leaf("""Figure 1 illustrates a motivating example that includes two
vulnerabilities detected by LARA in the firmware of the DLink DIR-882 router. The first vulnerability CVE-A 3 is triggered through the following steps: ❶ The attacker interacts
with the web interface (frontend) of the router DIR-882 to
configure the networksettings. Inside the SubnetMask field,
the attacker inputs an injection payload such as “;rm −rf /;".
❷ The frontend generates an HTTP request using the form
SetNetworkSettings and the key-value pairs encoding the form
data. In this case, SetNetworkSettings is filled into the URI [52]
field of the HTTP packet, while SubnetMask and the payload
3CVE-A is CVE-2022-28896 and CVE-B is CVE-2022-28901.
are filled into the body field as one of the key-value pairs
(“SubnetMask=';rm −rf /;'") encoded as form−data [22]. ❸ When
receiving the HTTP request, the backend of the router finds
the corresponding function to handle it according to the URI
value of the form. In this case, the function is sub_43AF7C. ❹
After sub_43AF7C receives the content of the HTTP request,
it extracts the values of the keys with specific functions. In
this case, the function is websGetVarString. ❺ The backend
processes the extracted values as a command and invokes
the function system to execute the command, allowing the
attacker to execute arbitrary code on the router.
The second vulnerability, CVE-B, can be triggered with the
following process: ① The form for this vulnerability is hidden,
which means there is no corresponding frontend code. Hence,
the attacker needs to generate the HTTP request and send it to
the backend directly. In this case, the form used by the HTTP
request is SetTriggerLEDBlink. ② According to the URI value
of the form, the backend invokes the function sub_4395CC
to handle the HTTP request. ③ After sub_4395CC receives
the HTTP request, it extracts the value for the key Blink. ④
The extracted value is processed to form a command with
sprintf and send to the function twsystem. It is worth noting that
the function twsystem is not in the main binary of the router
(prog.cgi), but instead resides in the shared library libcrm.so.
⑤ Inside the function twsystem, the user-controlled value is
executed by execv and the vulnerability is triggered.
Existing techniques have difficulty in identifying vulnerabilities similar to both CVE-A and CVE-B due to omitted
sources. To this end, we make an observation of why certain
sources are omitted from the examples in Figure 1.""")