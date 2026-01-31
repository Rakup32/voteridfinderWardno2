"""
ULTIMATE Roman to Devanagari Converter
Optimized for 8000+ voter names with intelligent phonetic engine
"""

import functools
import re
import json
import os

# ============================================================================
# COMPREHENSIVE NAME DATABASE - 500+ Common Names
# ============================================================================

COMMON_NAMES = {
    # Male First Names (A-Z)
    'abhay': 'अभय', 'abhishek': 'अभिषेक', 'abhiyan': 'अभियान',
    'achyut': 'अच्युत', 'achyuta': 'अच्युत',
    'aditya': 'आदित्य', 'adit': 'आदित',
    'agni': 'अग्नी', 'agniraj': 'अग्नीराज',
    'ajay': 'अजय', 'ajaya': 'अजय', 'ajit': 'अजित',
    'akhilesh': 'अखिलेश',
    'akash': 'आकाश', 'aakash': 'आकाश',
    'amar': 'अमर', 'amara': 'अमर', 'amardev': 'अमरदेव',
    'amit': 'अमित', 'amita': 'अमित',
    'amrit': 'अमृत', 'amrita': 'अमृत',
    'anil': 'अनिल', 'anila': 'अनिल',
    'anish': 'अनिष', 'anisha': 'अनिष',
    'anmol': 'अनमोल',
    'anup': 'अनुप', 'anupa': 'अनुप',
    'anurag': 'अनुराग', 'anuraga': 'अनुराग',
    'arjun': 'अर्जुन', 'arjuna': 'अर्जुन',
    'arvind': 'अरविन्द', 'aravind': 'अरविन्द',
    'aryal': 'अर्याल', 'aryala': 'अर्याल',
    'ashish': 'आशिष', 'asish': 'आशिष',
    'ashok': 'अशोक', 'asok': 'अशोक',
    'babu': 'बाबु', 'baboo': 'बाबु',
    'bahadur': 'बहादुर', 'bahadura': 'बहादुर',
    'bal': 'बाल', 'bala': 'बाल',
    'bhim': 'भीम', 'bhima': 'भीम',
    'bibek': 'बिबेक', 'vivek': 'बिबेक',
    'bijay': 'बिजय', 'vijay': 'बिजय', 'bijaya': 'बिजय',
    'bikash': 'बिकास', 'vikas': 'विकास', 'bikasa': 'बिकास',
    'bikram': 'बिक्रम', 'vikram': 'विक्रम',
    'binay': 'बिनय', 'binaya': 'बिनय',
    'binod': 'बिनोद', 'binoda': 'बिनोद',
    'bir': 'बीर', 'beer': 'बीर', 'vir': 'बीर',
    'bishnu': 'बिष्णु', 'vishnu': 'बिष्णु',
    'buddha': 'बुद्ध', 'budha': 'बुद्ध',
    'chandra': 'चन्द्र', 'candra': 'चन्द्र',
    'dal': 'दल', 'dala': 'दल',
    'dambar': 'दम्बर', 'dambara': 'दम्बर',
    'deepak': 'दीपक', 'dipak': 'दीपक', 'dipaka': 'दीपक',
    'deependra': 'दिपेन्द्र', 'dipendra': 'दिपेन्द्र',
    'desh': 'देश', 'desha': 'देश',
    'dev': 'देव', 'deva': 'देव',
    'dhan': 'धन', 'dhana': 'धन',
    'dharma': 'धर्म', 'dharama': 'धर्म',
    'dhir': 'धीर', 'dhira': 'धीर',
    'dinesh': 'दिनेश', 'dinesha': 'दिनेश',
    'dipendra': 'दिपेन्द्र',
    'ek': 'एक', 'eka': 'एक',
    'ganesh': 'गणेश', 'ganesha': 'गणेश',
    'ganga': 'गंगा', 'gangaa': 'गंगा',
    'gautam': 'गौतम', 'gautama': 'गौतम',
    'gokul': 'गोकुल', 'gokula': 'गोकुल',
    'gopal': 'गोपाल', 'gopala': 'गोपाल',
    'govinda': 'गोविन्द', 'gobinda': 'गोविन्द',
    'hari': 'हरि', 'hare': 'हरि',
    'hem': 'हेम', 'hema': 'हेम',
    'himal': 'हिमाल', 'himala': 'हिमाल',
    'hira': 'हिरा', 'hiraa': 'हिरा',
    'indra': 'इन्द्र', 'endra': 'इन्द्र',
    'jagat': 'जगत', 'jagata': 'जगत',
    'janak': 'जनक', 'janaka': 'जनक',
    'jay': 'जय', 'jaya': 'जय',
    'jit': 'जित', 'jita': 'जित',
    'jivan': 'जीवन', 'jeewan': 'जीवन',
    'kailash': 'कैलाश', 'kailasa': 'कैलाश',
    'kalyan': 'कल्याण', 'kalyana': 'कल्याण',
    'kamal': 'कमल', 'kamala': 'कमल',
    'karna': 'कर्ण', 'karana': 'कर्ण',
    'khadga': 'खड्ग', 'khadaga': 'खड्ग',
    'khim': 'खिम', 'khima': 'खिम',
    'kiran': 'किरण', 'kirana': 'किरण',
    'krishna': 'कृष्ण', 'krisna': 'कृष्ण',
    'kumar': 'कुमार', 'kumara': 'कुमार',
    'lal': 'लाल', 'lala': 'लाल',
    'laxman': 'लक्ष्मण', 'lakshman': 'लक्ष्मण',
    'lok': 'लोक', 'loka': 'लोक',
    'madan': 'मदन', 'madana': 'मदन',
    'magar': 'मगर', 'magara': 'मगर',
    'mahabir': 'महाबीर', 'mahavir': 'महाबीर',
    'mahendra': 'महेन्द्र', 'mahindra': 'महेन्द्र',
    'mahesh': 'महेश', 'mahesha': 'महेश',
    'man': 'मान', 'mana': 'मान',
    'mohan': 'मोहन', 'mohana': 'मोहन',
    'mukti': 'मुक्ति', 'mukta': 'मुक्ति',
    'mukunda': 'मुकुन्द', 'mukunda': 'मुकुन्द',
    'nabin': 'नबिन', 'nabina': 'नबिन',
    'nanda': 'नन्द', 'nandaa': 'नन्द',
    'narayan': 'नारायण', 'narayana': 'नारायण',
    'naresh': 'नरेश', 'naresha': 'नरेश',
    'nir': 'नीर', 'neera': 'नीर',
    'om': 'ओम', 'oma': 'ओम',
    'padam': 'पदम', 'padama': 'पदम',
    'parbat': 'पर्वत', 'parvat': 'पर्वत',
    'pawan': 'पवन', 'pavana': 'पवन',
    'prabhakar': 'प्रभाकर',
    'prakash': 'प्रकाश', 'prakas': 'प्रकाश',
    'pramod': 'प्रमोद', 'pramoda': 'प्रमोद',
    'prasad': 'प्रसाद', 'prasada': 'प्रसाद', 'prashad': 'प्रसाद',
    'purna': 'पूर्ण', 'poorna': 'पूर्ण',
    'pushkar': 'पुष्कर', 'puskara': 'पुष्कर',
    'rabi': 'रबि', 'rabia': 'रबि',
    'raj': 'राज', 'raaj': 'राज',
    'rajan': 'राजन', 'rajana': 'राजन',
    'rajendra': 'राजेन्द्र', 'rajindra': 'राजेन्द्र',
    'rajesh': 'राजेश', 'rajesha': 'राजेश',
    'ram': 'राम', 'rama': 'राम', 'raam': 'राम',
    'ramesh': 'रमेश', 'ramesha': 'रमेश',
    'ratna': 'रत्न', 'ratana': 'रत्न',
    'ravi': 'रवि', 'ravia': 'रवि',
    'rudra': 'रुद्र', 'rudara': 'रुद्र',
    'sagar': 'सागर', 'sagara': 'सागर',
    'sanjay': 'संजय', 'sanjaya': 'संजय',
    'sanjib': 'संजिब', 'sanjiva': 'संजिब',
    'sankar': 'संकर', 'sankara': 'संकर',
    'santosh': 'सन्तोष', 'santosa': 'सन्तोष',
    'sher': 'शेर', 'shera': 'शेर',
    'shiva': 'शिव', 'siva': 'शिव',
    'shyam': 'श्याम', 'shyama': 'श्याम', 'syam': 'श्याम',
    'siddhartha': 'सिद्धार्थ', 'sidharta': 'सिद्धार्थ',
    'subash': 'सुबास', 'subhash': 'सुभाष',
    'sujan': 'सुजन', 'sujana': 'सुजन',
    'suman': 'सुमन', 'sumana': 'सुमन',
    'sunil': 'सुनिल', 'sunila': 'सुनिल',
    'suraj': 'सूरज', 'suraja': 'सूरज',
    'surendra': 'सुरेन्द्र', 'surindra': 'सुरेन्द्र',
    'suresh': 'सुरेश', 'suresha': 'सुरेश',
    'surya': 'सूर्य', 'surja': 'सूर्य',
    'tej': 'तेज', 'teja': 'तेज',
    'til': 'तिल', 'tila': 'तिल',
    'tulsi': 'तुलसी', 'tulasi': 'तुलसी',
    'umesh': 'उमेश', 'umesha': 'उमेश',
    'upendra': 'उपेन्द्र', 'upindra': 'उपेन्द्र',
    'vijay': 'विजय', 'vijaya': 'विजय', 'bijay': 'बिजय',
    'vimal': 'विमल', 'bimal': 'विमल',
    'yam': 'याम', 'yama': 'याम',
    
    # Female First Names
    'aarati': 'आरती', 'arati': 'आरती', 'aarti': 'आरती',
    'aasha': 'आशा', 'asha': 'आशा', 'asa': 'आशा',
    'amrita': 'अमृता', 'amita': 'अमिता',
    'anita': 'अनिता', 'aneeta': 'अनिता',
    'anjali': 'अञ्जली', 'anjala': 'अञ्जली',
    'anju': 'अञ्जु', 'anjoo': 'अञ्जु',
    'anupama': 'अनुपमा',
    'anuradha': 'अनुराधा',
    'archana': 'अर्चना', 'archanaa': 'अर्चना',
    'asmita': 'अस्मिता', 'asmitaa': 'अस्मिता',
    'babita': 'बबिता', 'babitaa': 'बबिता',
    'barsha': 'वर्षा', 'varsha': 'वर्षा',
    'bina': 'बिना', 'binaa': 'बिना',
    'binita': 'बिनिता', 'binitaa': 'बिनिता',
    'bishnu': 'बिष्णु',
    'champa': 'चम्पा', 'campaa': 'चम्पा',
    'chandra': 'चन्द्रा', 'candra': 'चन्द्रा',
    'chandrakala': 'चन्द्रकला',
    'devi': 'देवी', 'devee': 'देवी',
    'dhan': 'धन', 'dhana': 'धन',
    'dil': 'दिल', 'dila': 'दिल',
    'durga': 'दुर्गा', 'durgaa': 'दुर्गा',
    'ganga': 'गंगा', 'gangaa': 'गंगा',
    'geeta': 'गीता', 'gita': 'गीता', 'gheeta': 'गीता',
    'goma': 'गोमा', 'gomaa': 'गोमा',
    'hema': 'हेमा', 'hemaa': 'हेमा',
    'indira': 'इन्दिरा', 'indiraa': 'इन्दिरा',
    'janaki': 'जानकी', 'janakee': 'जानकी',
    'jayanti': 'जयन्ती', 'jayantee': 'जयन्ती',
    'juna': 'जुना', 'junaa': 'जुना',
    'kala': 'काला', 'kaalaa': 'काला',
    'kali': 'काली', 'kaali': 'काली',
    'kalpa': 'कल्पा', 'kalpaa': 'कल्पा',
    'kamala': 'कमला', 'kamalaa': 'कमला', 'kamla': 'कमला',
    'kalpana': 'कल्पना', 'kalpanaa': 'कल्पना',
    'kanti': 'कान्ति', 'kaanti': 'कान्ति',
    'kopila': 'कोपिला', 'kopilaa': 'कोपिला',
    'krishna': 'कृष्णा', 'krisna': 'कृष्णा',
    'kumari': 'कुमारी', 'kumaari': 'कुमारी', 'kumaree': 'कुमारी',
    'laxmi': 'लक्ष्मी', 'lakshmi': 'लक्ष्मी', 'laxami': 'लक्ष्मी', 'laxmee': 'लक्ष्मी',
    'lila': 'लीला', 'leela': 'लीला', 'lilaa': 'लीला',
    'maina': 'मैना', 'mainaa': 'मैना',
    'mamata': 'ममता', 'mamataa': 'ममता',
    'mana': 'मना', 'manaa': 'मना',
    'mangala': 'मंगला', 'mangalaa': 'मंगला',
    'manju': 'मञ्जु', 'manjoo': 'मञ्जु',
    'maya': 'माया', 'maayaa': 'माया',
    'meena': 'मीना', 'mina': 'मीना', 'minaa': 'मीना',
    'nanda': 'नन्दा', 'nandaa': 'नन्दा',
    'nani': 'नानी', 'naanee': 'नानी',
    'nanu': 'नानु', 'nanoo': 'नानु',
    'nirmala': 'निर्मला', 'nirmalaa': 'निर्मला',
    'parbati': 'पार्वती', 'parvati': 'पार्वती', 'parvatee': 'पार्वती',
    'phulmaya': 'फूलमाया', 'phulmayaa': 'फूलमाया',
    'pramila': 'प्रमिला', 'pramilaa': 'प्रमिला',
    'prem': 'प्रेम', 'prema': 'प्रेम',
    'punam': 'पूनम', 'poonam': 'पूनम',
    'purnima': 'पूर्णिमा', 'poornima': 'पूर्णिमा',
    'pushpa': 'पुष्पा', 'puspaa': 'पुष्पा',
    'radha': 'राधा', 'raadhaa': 'राधा',
    'rajani': 'रजनी', 'rajanee': 'रजनी',
    'rani': 'रानी', 'raanee': 'रानी',
    'ratna': 'रत्ना', 'ratnaa': 'रत्ना',
    'rekha': 'रेखा', 'rekhaa': 'रेखा',
    'renuka': 'रेनुका', 'renukaa': 'रेनुका',
    'rita': 'रीता', 'reeta': 'रीता', 'ritaa': 'रीता',
    'rupa': 'रुपा', 'roopa': 'रुपा', 'rupaa': 'रुपा',
    'sabita': 'सबिता', 'sabitaa': 'सबिता', 'savita': 'सबिता',
    'sabitra': 'सबित्रा', 'sabitraa': 'सबित्रा',
    'sangita': 'संगीता', 'sangeeta': 'संगीता', 'sangeetaa': 'संगीता',
    'sani': 'सानी', 'saani': 'सानी',
    'saraswati': 'सरस्वती', 'saraswoti': 'सरस्वती', 'sarasvati': 'सरस्वती',
    'saru': 'सरु', 'saroo': 'सरु',
    'shanta': 'शान्ता', 'santaa': 'शान्ता', 'shantaa': 'शान्ता',
    'sharmila': 'शर्मिला', 'sharmilaa': 'शर्मिला',
    'shila': 'शिला', 'silaa': 'शिला',
    'shiva': 'शिवा', 'sivaa': 'शिवा',
    'sita': 'सीता', 'seeta': 'सीता', 'sitaa': 'सीता',
    'srijana': 'सृजना', 'srijanaa': 'सृजना',
    'suk': 'सुक', 'suka': 'सुक',
    'sumitra': 'सुमित्रा', 'sumitraa': 'सुमित्रा',
    'sunita': 'सुनिता', 'sunitaa': 'सुनिता', 'suneeta': 'सुनिता',
    'sushila': 'सुशिला', 'susilaa': 'सुशिला',
    'tara': 'तारा', 'taraa': 'तारा',
    'tika': 'टिका', 'teeka': 'टिका',
    'tilak': 'तिलक', 'tilaka': 'तिलक',
    'tul': 'तुल', 'tula': 'तुल',
    'tulasa': 'तुलसा', 'tulasaa': 'तुलसा',
    'uma': 'उमा', 'umaa': 'उमा',
    'usha': 'उषा', 'usaa': 'उषा',
    
    # Surnames - Comprehensive List
    'aale': 'आले', 'ale': 'आले',
    'acharya': 'आचार्य', 'acarya': 'आचार्य',
    'adhikari': 'अधिकारी', 'adhikaari': 'अधिकारी', 'adhikary': 'अधिकारी',
    'agrawal': 'अग्रवाल', 'agrawala': 'अग्रवाल',
    'ale': 'आले', 'aale': 'आले',
    'amatya': 'अमात्य', 'amathya': 'अमात्य',
    'aryal': 'अर्याल', 'aryala': 'अर्याल',
    'bajracharya': 'बज्राचार्य', 'bajracarya': 'बज्राचार्य',
    'baidya': 'वैद्य', 'vaidya': 'वैद्य',
    'basnet': 'बस्नेत', 'basneta': 'बस्नेत',
    'bastola': 'बस्तोला', 'bastolaa': 'बस्तोला',
    'bhandari': 'भण्डारी', 'bhandaari': 'भण्डारी', 'bhandary': 'भण्डारी',
    'bhattarai': 'भट्टराई', 'bhattrai': 'भट्टराई', 'bhatarai': 'भट्टराई',
    'bhote': 'भोटे', 'bhotey': 'भोटे',
    'bhujel': 'भुजेल', 'bhujela': 'भुजेल',
    'bohora': 'बोहोरा', 'bohra': 'बोहोरा',
    'budha': 'बुढा', 'budhaa': 'बुढा',
    'budhathoki': 'बुढाथोकी', 'budhathokee': 'बुढाथोकी',
    'chaudhary': 'चौधरी', 'caudhary': 'चौधरी', 'caudharee': 'चौधरी',
    'chettri': 'छेत्री', 'chhetri': 'छेत्री', 'chetri': 'छेत्री',
    'dahal': 'दाहाल', 'dahaal': 'दाहाल',
    'dangol': 'दंगोल', 'dangola': 'दंगोल',
    'devkota': 'देवकोटा', 'debkota': 'देवकोटा', 'devakota': 'देवकोटा',
    'dhital': 'ढिटाल', 'dhitaal': 'ढिटाल',
    'dura': 'दुरा', 'duraa': 'दुरा',
    'gautam': 'गौतम', 'gautama': 'गौतम',
    'giri': 'गिरी', 'giree': 'गिरी',
    'gurung': 'गुरुङ', 'gurunga': 'गुरुङ',
    'gyawali': 'ग्यावली', 'gyawaly': 'ग्यावली',
    'joshi': 'जोशी', 'josi': 'जोशी', 'josee': 'जोशी',
    'kafle': 'काफ्ले', 'kafley': 'काफ्ले',
    'karki': 'कार्की', 'karkee': 'कार्की',
    'kc': 'के.सी.', 'kc': 'केसी',
    'khadka': 'खड्का', 'khadaka': 'खड्का',
    'khatiwada': 'खतिवडा', 'khatiwadaa': 'खतिवडा',
    'khatri': 'खत्री', 'khatriy': 'खत्री', 'khatree': 'खत्री',
    'koirala': 'कोइराला', 'koiraala': 'कोइराला',
    'kunwar': 'कुँवर', 'kunwor': 'कुँवर',
    'lama': 'लामा', 'laama': 'लामा',
    'lamichhane': 'लामिछाने', 'lamichane': 'लामिछाने',
    'limbu': 'लिम्बू', 'limboo': 'लिम्बू',
    'magar': 'मगर', 'magara': 'मगर',
    'maharjan': 'महर्जन', 'mahajan': 'महर्जन',
    'mainali': 'मैनाली', 'mainalee': 'मैनाली',
    'malla': 'मल्ल', 'mallah': 'मल्ल',
    'mishra': 'मिश्र', 'misra': 'मिश्र',
    'nepal': 'नेपाल', 'nepaal': 'नेपाल',
    'nepali': 'नेपाली', 'nepaali': 'नेपाली',
    'newar': 'नेवार', 'newara': 'नेवार',
    'oli': 'ओली', 'olee': 'ओली',
    'pandey': 'पाण्डेय', 'pande': 'पाण्डेय', 'pandé': 'पाण्डेय',
    'pant': 'पन्त', 'panta': 'पन्त',
    'panth': 'पन्थ', 'pantha': 'पन्थ',
    'parajuli': 'पराजुली', 'parajulee': 'पराजुली',
    'pathak': 'पाठक', 'pathaka': 'पाठक',
    'pokharel': 'पोखरेल', 'pokhrel': 'पोखरेल',
    'poudel': 'पौडेल', 'paudel': 'पौडेल', 'poudyal': 'पौडेल',
    'pradhan': 'प्रधान', 'pradhaan': 'प्रधान',
    'rai': 'राई', 'raai': 'राई', 'raee': 'राई',
    'rajbhandari': 'राजभण्डारी', 'rajbhandary': 'राजभण्डारी',
    'rana': 'राना', 'raana': 'राना',
    'regmi': 'रेग्मी', 'regamee': 'रेग्मी',
    'rimal': 'रिमाल', 'rimaal': 'रिमाल',
    'rijal': 'रिजाल', 'rijaal': 'रिजाल',
    'sahi': 'साही', 'saahee': 'साही',
    'sapkota': 'सापकोटा', 'sapkotaa': 'सापकोटा',
    'shah': 'शाह', 'saha': 'शाह',
    'shahi': 'शाही', 'sahee': 'शाही',
    'shakya': 'शाक्य', 'sakya': 'शाक्य',
    'sharma': 'शर्मा', 'sarma': 'शर्मा', 'sharmaa': 'शर्मा',
    'sherpa': 'शेर्पा', 'sharpa': 'शेर्पा',
    'shrestha': 'श्रेष्ठ', 'srestha': 'श्रेष्ठ', 'shrestho': 'श्रेष्ठ',
    'singh': 'सिंह', 'simha': 'सिंह', 'singha': 'सिंह',
    'subedi': 'सुवेदी', 'subedee': 'सुवेदी',
    'sunuwar': 'सुनुवार', 'sunwar': 'सुनुवार',
    'tamang': 'तामाङ', 'tamanga': 'तामाङ', 'tamaang': 'तामाङ',
    'thakuri': 'ठकुरी', 'thakuree': 'ठकुरी',
    'thapa': 'थापा', 'thaapa': 'थापा',
    'tiwari': 'तिवारी', 'tiwary': 'तिवारी', 'tiwaree': 'तिवारी',
    'tuladhar': 'तुलाधर', 'tuladhara': 'तुलाधर',
    'upadhyay': 'उपाध्याय', 'upadhyaya': 'उपाध्याय',
}

# ============================================================================
# PHONETIC ENGINE - Devanagari Components
# ============================================================================

VOWELS = {
    'a': 'अ', 'aa': 'आ', 'i': 'इ', 'ii': 'ई', 'ee': 'ई',
    'u': 'उ', 'uu': 'ऊ', 'oo': 'ऊ',
    'e': 'ए', 'ai': 'ऐ', 'o': 'ओ', 'au': 'औ',
    'ri': 'ऋ', 'rii': 'ॠ',
}

MATRA = {
    'a': '', 'aa': 'ा', 'i': 'ि', 'ii': 'ी', 'ee': 'ी',
    'u': 'ु', 'uu': 'ू', 'oo': 'ू',
    'e': 'े', 'ai': 'ै', 'o': 'ो', 'au': 'ौ',
    'ri': 'ृ', 'rii': 'ॄ',
}

CONSONANTS = {
    # Aspirated (must come before non-aspirated)
    'kh': 'ख', 'gh': 'घ', 'chh': 'छ', 'jh': 'झ',
    'th': 'ठ', 'dh': 'ढ', 'tha': 'थ', 'dha': 'ध',
    'ph': 'फ', 'bh': 'भ',
    # Consonants
    'k': 'क', 'g': 'ग', 'ng': 'ङ',
    'ch': 'च', 'chh': 'छ', 'j': 'ज', 'ny': 'ञ',
    't': 'ट', 'd': 'ड', 'n': 'ण',
    'ta': 'त', 'da': 'द', 'na': 'न',
    'p': 'प', 'b': 'ब', 'm': 'म',
    'y': 'य', 'r': 'र', 'l': 'ल', 'w': 'व', 'v': 'व',
    'sh': 'श', 'shh': 'ष', 's': 'स', 'h': 'ह',
    # Conjuncts
    'ksh': 'क्ष', 'tr': 'त्र', 'gya': 'ज्ञ', 'gy': 'ज्ञ',
}

NUMBERS = {
    '0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
    '5': '५', '6': '६', '7': '७', '8': '८', '9': '९',
}

# ============================================================================
# ADVANCED LEARNING SYSTEM
# ============================================================================

# Cache for learned names from actual data
_learned_names_cache = {}
_cache_loaded = False

def load_voter_names_database():
    """Load names from voter database if available"""
    global _learned_names_cache, _cache_loaded
    
    if _cache_loaded:
        return
    
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'voter_names_db.json')
        if os.path.exists(db_path):
            with open(db_path, 'r', encoding='utf-8') as f:
                _learned_names_cache = json.load(f)
            print(f"✓ Loaded {len(_learned_names_cache)} names from voter database")
    except Exception as e:
        print(f"Note: Could not load voter database: {e}")
    finally:
        _cache_loaded = True

# ============================================================================
# CONVERSION FUNCTIONS
# ============================================================================

@functools.lru_cache(maxsize=5000)
def roman_to_devanagari(text):
    """
    Convert Roman text to Devanagari.
    Priority: Learned DB > Common Names > Phonetic
    """
    if not text:
        return text
    
    text = text.strip().lower()
    
    # Priority 1: Check learned database
    load_voter_names_database()
    if text in _learned_names_cache:
        return _learned_names_cache[text]
    
    # Priority 2: Check common names
    if text in COMMON_NAMES:
        return COMMON_NAMES[text]
    
    # Priority 3: Multi-word handling
    words = text.split()
    if len(words) > 1:
        converted_words = []
        for word in words:
            # Check each word in learned DB
            if word in _learned_names_cache:
                converted_words.append(_learned_names_cache[word])
            elif word in COMMON_NAMES:
                converted_words.append(COMMON_NAMES[word])
            else:
                converted_words.append(_transliterate_phonetic(word))
        return ' '.join(converted_words)
    
    # Priority 4: Phonetic conversion
    return _transliterate_phonetic(text)


def _transliterate_phonetic(word):
    """Advanced phonetic transliteration"""
    if not word:
        return word
    
    result = []
    i = 0
    
    while i < len(word):
        matched = False
        
        # Try longest match first
        for length in range(min(4, len(word) - i), 0, -1):
            substr = word[i:i+length]
            
            # Numbers
            if substr in NUMBERS:
                result.append(NUMBERS[substr])
                i += length
                matched = True
                break
            
            # Consonants (with aspiration check)
            if substr in CONSONANTS:
                result.append(CONSONANTS[substr])
                # Check for vowel
                if i + length < len(word):
                    next_pos = i + length
                    for vlen in range(min(2, len(word) - next_pos), 0, -1):
                        vsub = word[next_pos:next_pos+vlen]
                        if vsub in MATRA:
                            result.append(MATRA[vsub])
                            i += length + vlen
                            matched = True
                            break
                    if matched:
                        break
                    # Check if next is consonant (add halant)
                    for clen in range(min(3, len(word) - next_pos), 0, -1):
                        if word[next_pos:next_pos+clen] in CONSONANTS:
                            result.append('्')
                            break
                i += length
                matched = True
                break
            
            # Vowels
            if substr in VOWELS:
                result.append(VOWELS[substr])
                i += length
                matched = True
                break
        
        if not matched:
            result.append(word[i])
            i += 1
    
    return ''.join(result)


def is_devanagari(text):
    """Check if text contains Devanagari"""
    if not text:
        return False
    return bool(re.search(r'[\u0900-\u097F]', text))


def smart_convert(text):
    """Smart conversion - only convert Roman text"""
    if not text:
        return text
    
    text = text.strip()
    
    if is_devanagari(text):
        return text
    
    return roman_to_devanagari(text)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    test_cases = [
        # Common names
        "ram", "krishna", "sita", "hari", "shyam",
        # Surnames
        "shrestha", "tamang", "gurung", "magar", "thapa",
        # Full names
        "ram bahadur shrestha",
        "krishna prasad sharma",
        "sita devi tamang",
        # Less common
        "achyut", "dinesh", "anmol",
    ]
    
    print("=" * 70)
    print("ULTIMATE ROMAN TO NEPALI CONVERTER TEST")
    print(f"Database: {len(COMMON_NAMES)} common names + learned names")
    print("=" * 70)
    
    for test in test_cases:
        result = roman_to_devanagari(test)
        print(f"{test:30} → {result}")