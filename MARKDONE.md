# MARKDONE — SmartDispatch code ka personal Hinglish walkthrough

> Yeh file tumhari personal understanding ke liye hai. Yeh required submission notes ka replacement nahi hai. Isme code ko simple Hinglish mein samjhaya gaya hai, taaki tum khud explain kar sako ki dispatch logic kaise kaam karta hai.

## 1. Project ka main idea

Socho ek food-delivery order aaya hai. Program ko decide karna hai ki available delivery partners mein se kisko order diya jaaye aur order approx kab deliver hoga.

Is project mein actual Zomato data, live GPS ya map API use nahi hoti. Data synthetic/sample hai. Program mainly teen cheezen karta hai:

1. Order, partner aur time data valid hai ya nahi check karta hai.
2. Jo partners eligible hain unke liye pickup time aur delivery ETA calculate karta hai.
3. Sabse kam ETA wala partner select karta hai; exact tie ho to partner ID ke alphabetical/lexicographical order se decide karta hai.

Cancellation ke liye alag function hai, jo cancelled order ka workload partner se release karta hai aur ek hi cancellation event ko dobara apply nahi hone deta.

## 2. Program ka data flow

Offline demo ka flow yeh hai:

main.py → fixtures.py se sample data leta hai → assign_order() call karta hai → har partner ka estimate_eta() nikalta hai → best eligible partner return hota hai.

- models.py mein new_order() aur new_partner() sample record banane ke helpers hain.
- fixtures.py sample order, partners, workload aur travel-time mapping banata hai.
- main.py demo ko start karke result print karta hai.
- service.py mein actual decision logic hai; isi file mein core fix kiya gaya.

## 3. service.py ke imports kyun hain?

- Mapping: check karne ke liye ki input dict jaisa key/value record hai. Isse malformed input par .get() call karke crash hone se bach sakte hain.
- deepcopy: cancellation ke waqt original partner record ko mutate na karke uski alag copy update karne ke liye.
- math: NaN aur infinity jaise invalid number values ko pehchanne ke liye math.isfinite() use hota hai.
- Real: valid numeric types identify karne ke liye. bool Python mein int ka subtype hota hai (True == 1), isliye code bool ko separately reject karta hai.

## 4. Validation helpers

### _is_non_negative_number(value)

Yeh check karta hai ki value:

- number ho;
- True/False na ho;
- negative na ho;
- NaN ya infinity na ho.

Valid examples: 0, 8, 2.5.  
Invalid examples: -1, "8", True, float('nan'), float('inf').

try/except isliye hai ki bahut hi bade number ko finite-check karte waqt Python overflow/type error de sakta hai. Aisi value ko crash karne ke bajay invalid maana jaata hai.

### _is_identifier(value)

Identifier non-empty string hona chahiye. "P-2" valid hai; empty string, spaces-only string, None, ya number invalid hain. Isse partner ID, order ID aur zone values predictable rehte hain.

### _invalid_estimate(partner_id=None)

Invalid candidate ke liye ek consistent result deta hai:

- partner ID agar mil sake;
- eta_minutes = None;
- eligible = False.

None ka matlab: is candidate se reliable ETA nahi nikala ja sakta.

## 5. estimate_eta(order, partner, travel, now=0) — ek partner ka ETA

Is function ka kaam sirf ek order aur ek partner ke liye ETA nikalna hai.

### Step-by-step

1. Record types check: order aur partner dict-like (Mapping) hone chahiye. Warna invalid estimate return hota hai.
2. IDs / zones validate: order ID, restaurant ID, destination zone, partner ID aur partner zone non-empty strings hone chahiye.
3. Time values validate: current time (now), prep time aur partner workload non-negative finite numbers hone chahiye.
4. Travel mapping validate: travel data dict-like honi chahiye.
5. Dono travel legs dhoondho:
   - leg1: partner zone se restaurant tak.
   - leg2: restaurant se customer/destination zone tak.
6. Missing/invalid leg reject: route missing ho to zero assume nahi hota; estimate ineligible hota hai.
7. Formula apply:
   - pickup = now + leg1 + workload_minutes
   - eta = pickup + prep_minutes + leg2
8. Result mein partner ID, pickup, ETA aur eligible=True aata hai.

### Demo ke numbers se

Order O-7 ka restaurant R-2, destination Z-9, prep time 10 min hai. Partner P-2 zone Z-1 mein hai, uska workload 5 min hai. Travel Z-1 → R-2 = 8 min aur R-2 → Z-9 = 12 min hai. now default 0 hai.

- Pickup = 0 + 8 + 5 = 13 min.
- ETA = 13 + 10 + 12 = 35 min.

Yeh batata hai ki partner restaurant tak kab pahunch sakta hai aur customer tak total estimate kab hoga.

## 6. _valid_partner_capacity(partner) — partner lene layak hai?

assign_order() se pehle yeh eligibility helper check hota hai:

- Partner record dict-like ho.
- active exactly True ho. "yes", 1, ya None ko active nahi maana jaata.
- capacity positive integer ho; boolean, float, zero ya negative capacity valid nahi.
- active_order_ids list ho.
- Active orders ki count capacity se kam ho.

Example: capacity 2, active orders ['OLD-1'] → ek slot bacha hai, so capacity ke hisaab se eligible. Capacity 1, active orders ['OLD-1'] → full hai, so reject.

Capacity ko active-order count se check kiya jaata hai; isliye current order assign karne se pehle hi full partner filter ho jaata hai.

## 7. assign_order(order, partners, travel, now=0) — final partner choose karna

Yeh main dispatcher function hai.

1. Order mapping ho to uska order ID result ke liye nikaalta hai.
2. Partners list/tuple na ho to empty list jaisa treat karta hai, taaki loop safely skip ho.
3. Har partner par _valid_partner_capacity() chalata hai. Inactive/full/invalid partners ko seedha skip karta hai.
4. Baaki partners ke liye estimate_eta() call hota hai.
5. Sirf eligible=True estimates options mein jaate hain.
6. Agar options empty hai, order unassigned return hota hai: partner_id=None, eta_minutes=None, aur reason batata hai ki eligible partner ya valid time data nahi mila.
7. Warna min() se best option chunta hai. Key (eta_minutes, partner_id) hai:
   - Pehle kam ETA jeetega.
   - ETA equal ho to chhota partner ID jeetega.
8. Assigned result mein order ID, partner ID, pickup time, ETA aur reason='assigned' hota hai.

Is tuple-key ka fayda: tie-breaking deterministic hai. Input list ka order badalne par bhi same ETA aur IDs ke liye same winner aana chahiye.

## 8. process_cancellation(partner, order_id, event_id) — cancellation ek hi baar

Cancellation ka matlab hai partner ke active orders mein se order hataana aur us order ka remaining workload ghataana.

1. deepcopy(partner) original record ki copy banata hai; function caller ke original object ko in-place change nahi karta.
2. active_order_ids aur processed_cancellation_ids valid lists na hon to safe empty lists set hoti hain.
3. Agar event_id pehle se processed_cancellation_ids mein hai, copy ko waise hi return kar deta hai. Isse duplicate cancellation workload dobara release nahi karti.
4. Agar order active list mein hai to us order ko remove karta hai.
5. minutes_by_order mapping se us order ke minutes leta hai. Workload aur per-order minutes valid non-negative numbers hon to naya workload max(0, old_workload - order_minutes) hota hai. max(0, ...) negative workload prevent karta hai.
6. Event ID processed list mein add hoti hai aur updated copy return hoti hai.

Example: workload 9 min, order O1 workload 9 min, cancellation C1 → pehli call par workload 0 ho jaata hai aur C1 record hota hai. Wahi C1 dobara aaye to function kuch subtract nahi karta aur list mein duplicate C1 nahi add karta.

## 9. Baaki files mein kya hai?

- models.py: new_order() aur new_partner() dictionaries banate hain. Defaults jaise active=True, capacity, empty active-orders list aur zero workload yahin se aate hain.
- fixtures.py: demo ka fixed synthetic example banata hai. P-2 ke travel/workload aur P-1 ke travel/workload deta hai.
- main.py: sample_inputs() leta hai, assign_order() call karta hai, result print karta hai.
- tests/: expected behavior check karte hain—formula, missing routes, active/capacity, tie-break, invalid values, cancellation. Purane tests ko badla ya weaken nahi kiya; naye regression cases alag file mein add kiye.
- README.md, STUDENT_START_HERE.md, STUDENT_PROBLEM_STATEMENT.md: challenge ka setup, requirements aur deliverables batate hain.
- approach.md, challenges.md, optimizations.md, TESTING.md, DISPATCH_NOTES.md: assignment ke required evidence/engineering notes hain.
- GEMINI_HANDOFF.md: doosre LLM ko current project status aur pending work samjhane ke liye handoff note hai.

## 10. Is session mein kya change hua?

- Core logic service.py mein update hui: input validation, candidate eligibility/capacity filtering, deterministic best selection, aur duplicate cancellation protection.
- Required notes (approach.md, challenges.md, optimizations.md, TESTING.md, DISPATCH_NOTES.md) actual recorded work/results ke basis par fill kiye gaye.
- Gemini ke liye GEMINI_HANDOFF.md banaya gaya.
- Yeh personal walkthrough ab MARKDONE.md ke roop mein add ho raha hai.
- Koi optional stretch feature nahi add kiya.

## 11. Verify kiye gaye results

- Code change se pehle: python -m pytest -q → 65 failed, 164 passed.
- Code change ke baad: python -m pytest -q → 233 passed.
- python -m main → order O-7 partner P-2 ko assign hua, pickup 13 min, ETA 35 min.
- git diff --check → whitespace issue nahi.
- Python version: 3.14.7. python -m pip install -r requirements-dev.txt chalaya; pytest 9.1.1 pehle se installed tha aur requirement satisfy karta tha.
- GitHub PR/CI abhi complete nahi hua. Visible tests pass hona achha checkpoint hai, lekin final submission ke liye baaki checklist aur PR steps bhi complete karne hain.

## 12. Tum khud kaise samjhaoge?

Agar mentor pooche “yeh method kyun use kiya?”, apne words mein yeh points explain kar sakte ho:

- Missing travel ko zero nahi maana, kyunki zero se fake fast ETA ban sakta hai.
- Booleans reject kiye, kyunki Python mein True integer jaisa behave karta hai aur galti se valid minute ban sakta hai.
- Har candidate pehle eligibility check hoti hai; warna inactive ya full partner select ho sakta hai.
- min((ETA, partner_id)) se lowest ETA aur stable tie-break ek saath hota hai.
- Cancellation event ID pehle check karte hain, taaki duplicate event workload/capacity dobara release na kare.
- Deep copy isliye, taaki cancellation function original input record ko chupke se mutate na kare.

Is file ko padhkar har function ko apne example se dobara samjhana practice karo. Agar kisi line ka meaning unclear ho, pehle us line aur uske test ka relationship dekho; sirf result ya code copy karna understanding nahi hoti.
# Part 2 — Choices ka reason aur alternatives

Is section mein “code kya karta hai” ke saath “yeh tareeqa kyun chuna” bhi samjho. Alternatives har project mein galat nahi hote; yahan chosen design current requirements ke liye seedha aur safe hai.

## Mapping kyun?

Order, partner aur travel records key/value data hain. Mapping check karne ke baad hi .get() use karte hain. Agar input None ya string ho, seedha .get() crash kar sakta hai. Sirf dict check karne ke bajay Mapping use karna read-only ya custom mapping ko bhi support karta hai.

## Real + bool rejection kyun?

Real numbers ko identify karne ka Python interface hai. Lekin bool Python mein int ka subtype hai; True ko galti se 1 minute maana ja sakta hai. Isliye pehle numeric type check aur alag bool rejection hai. Supplied inputs/tests int/float values use karte hain; Decimal jaisa type future contract mein aaye to validator ko adjust karna padega.

## Negative, NaN, infinity aur huge number kyun reject?

Duration negative nahi ho sakti. NaN normal number comparison nahi deta, infinity meaningful ETA nahi hai, aur bahut bade integer ko math.isfinite mein badalne se overflow ho sakta hai. Helper inhe invalid banata hai aur overflow/type error par bhi crash hone ke bajay False deta hai.

String "10" ko number mein convert karna ek alternative tha. Lekin coercion malformed input ko chhupa sakti hai. Is task mein strict reject chuna, jo acceptance tests ke behavior se match karta hai.

## Missing route ko zero kyun nahi maana?

Travel mapping mein route absent ho to lookup None deta hai. Zero use karne se fake instant-travel estimate ban sakta hai aur galat partner select ho sakta hai. Isliye candidate ineligible hota hai jab tak dono routes na milen.

Tuple key (start, end) se route direction clear hoti hai. Z-1 se R-2 aur R-2 se Z-9 do alag travel entries hain; ek hone se doosri assume nahi hoti.

## Identifier string kyun?

IDs aur zones mapping keys hain; partner ID ETA tie-break mein compare hoti hai. Non-empty strings consistent matching/order deti hain. Kisi bhi object ko ID maan lene se comparison ya route lookup inconsistent ho sakta hai. Agar project contract numeric IDs allow kare, validation aur tie-break rule ko saath update karna hoga.

## Eligibility ETA se pehle kyun?

Inactive ya full partner ka ETA nikalna mumkin hai, par order dena allowed nahi. Isliye assign_order pehle status/capacity filter karta hai, phir sirf bache partners ka ETA nikalta hai. Isse ineligible candidates par unnecessary work aur mixed logic dono kam hote hain.

Capacity positive integer honi chahiye; bool ko int subtype hone ke bawajood reject karte hain. Active-order count capacity se kam hona chahiye. Current data contract active_order_ids ko list expect karta hai.

## options list aur min() kyun, sort kyun nahi?

options mein valid ETA estimates store hote hain. Humein sirf winner chahiye, sab candidates ka sorted order nahi. min() key=(eta_minutes, partner_id) ek pass mein lowest ETA chunta hai aur tie ko partner ID se settle karta hai. Full sort bhi possible tha, par final ordering ki zaroorat nahi thi.

IDs strings validate hote hain, isliye tie-break consistent rehta hai. Yeh deterministic hai: input list ka order badle tab bhi same ETA/ID candidate winner hoga.

## Unassigned reason kyun?

No-candidate result mein partner_id aur ETA None ke saath readable reason diya jaata hai. Har candidate ko alag reason dena optional stretch feature tha, isliye woh add nahi kiya.

## deepcopy aur cancellation list kyun?

deepcopy partner ki independent copy banata hai. Directly original object mutate karne par doosri jagah use ho raha data chupke se badal sakta tha. Isliye copy update karke return hoti hai.

processed_cancellation_ids list starter model mein pehle se hai. Naya event process karke ID append hoti hai; repeat event ID milte hi function return kar deta hai. Is simple in-memory project ke liye list enough hai. Bahut bade persistent system mein database uniqueness constraint ya set-based storage consider ho sakta hai, lekin yahan zaroorat se zyada complexity hoti.

max(0, workload - order_minutes) se workload negative nahi hota. Agar workload record invalid ho, code us par arithmetic nahi karta. Event ID ki alag format validation abhi nahi hai, kyunki current acceptance requirement duplicate processing rokna hai.

# Part 3 — Required paanch Markdown files ka matlab

Yeh paanch files paanch alag sawalon ke jawab deti hain. Same test result reference ho sakta hai, lekin har file ka focus alag hai.

## approach.md — Kaam ko kaise samjha aur solve kiya?

- Baseline: editing se pehle command, Python version, exact test summary, demo output.
- Code flow: models, fixtures, main aur service ka role.
- Investigation: symptom, test evidence aur root cause.
- Decisions: kya badla aur kyun, jaise validation, eligibility aur duplicate-event guard.
- Verification: commands ke actual results aur pending limitations.

Isme engineering decisions/evidence chahiye, private reasoning transcript nahi.

## challenges.md — Kya confusing tha, debugging kaise ki?

- Actual issue: failures invalid times, eligibility/capacity aur duplicate cancellations mein the.
- Evidence: baseline mein 65 failed, 164 passed aur relevant test names.
- Koshish: baseline run, assertions padhna, failure ko service function tak trace karna, phir full suite rerun karna.
- Resolution: kis root cause ke liye kaunsi change hui.
- Proof: final 233 tests pass.
- Remaining challenge: GitHub CI, hidden checks aur PR pending.

Challenge invent nahi karna; jo actual evidence hai wahi likhna.

## optimizations.md — Kya improve kiya aur kya nahi?

- Objective correctness tha, speed nahi.
- Options compare: strict validation ya coercion; min ya sorting; deepcopy ya original object mutation; simple scan ya complex data structure.
- Implemented: reusable validator, eligibility helper, duplicate cancellation check.
- Trade-offs: strict validation malformed strings reject karti hai; linear candidate scan simple hai, lekin huge workload par performance measure karni hogi.
- Koi benchmark nahi hua, isliye speedup claim nahi hai.

## TESTING.md — Kaunse cases ka evidence hai?

Har row mein scenario/input, expected behavior, actual test outcome aur test name hota hai. Yahan missing routes, invalid times, inactive/full partners, tie-break aur duplicate cancellation documented hain. Recorded result 233 passed hai.

tests/test_regressions.py mein chaar naye regression cases add hue. Purane tests ko change ya weaken nahi kiya. GitHub CI aur hidden tests abhi pending hain.

## DISPATCH_NOTES.md — Formula ko concrete example se dikhao

- Worked ETA: O-7 aur P-2 values se pickup 13, ETA 35.
- No eligible partner: capacity 1 aur ek existing active order, to partner full aur order unassigned.
- Teen edge cases: missing route, invalid time, duplicate cancellation.
- Assumptions: lexicographic tie-break, workload formula, active order count se capacity, event idempotency.
- Limitations: visible suite pass; PR CI/hidden checks pending.

# Personal MARKDONE vs required docs

MARKDONE tumhara learning guide hai: methods aur design choices ko detail mein samjhata hai. Paanch required docs submission/evaluation notes hain aur concise, evidence-based hone chahiye. MARKDONE ko unmein copy karna zaroori nahi. Isse concept samajhkar required notes ko apne actual experience aur apne words ke saath review karo.

# Current completion status

- service.py ke core changes complete.
- Visible tests: 233 passed.
- Demo: O-7 ko P-2 assign, pickup 13, ETA 35.
- Paanch required notes aur Gemini handoff prepared.
- Optional stretch feature nahi kiya.
- Naya tests/test_regressions.py add hua; existing test files unchanged rahe.
- GitHub pull request, uska CI result aur hidden evaluator checks pending.

## Start karne ka easy tareeqa

Agar poori file ek saath lambi lage, is order mein padho:

1. Pehle main idea aur data flow samjho.
2. Phir ETA formula aur demo example dekho.
3. Uske baad partner filtering aur assign_order() samjho.
4. Cancellation ko alag topic ki tarah padho.
5. Aakhir mein “kyun yeh choice?” aur paanch Markdown files wali guide dekho.

Har technical naam ke baad socho: input kya hai, check kya hota hai, aur output kya milta hai?

## Ek poora demo run, shuru se result tak

main.py direct run hota hai, isliye sample_inputs() call hota hai. fixtures.py ek order, do partners aur travel-time mapping deta hai. Phir main.py assign_order(order, partners, travel) call karta hai.

| Kram | Kya hota hai | P-2 | P-1 |
|---|---|---:|---:|
| 1 | Partner active hai? | Haan | Haan |
| 2 | Capacity mein jagah hai? | Capacity 2, active orders 1 — jagah hai | Capacity 2, active orders 0 — jagah hai |
| 3 | Restaurant tak travel route? | 8 min | 12 min |
| 4 | Restaurant se destination tak route? | 12 min | 12 min |
| 5 | Pickup = now + first travel + workload | 0 + 8 + 5 = 13 | 0 + 12 + 2 = 14 |
| 6 | ETA = pickup + preparation + second travel | 13 + 10 + 12 = 35 | 14 + 10 + 12 = 36 |

Dono candidates valid hain. assign_order() unke estimates options list mein rakhta hai. min() ETA pe compare karta hai: 35, 36 se chhota hai, isliye P-2 choose hota hai. Return dictionary mein order_id O-7, partner_id P-2, pickup_minutes 13, eta_minutes 35, aur reason assigned hota hai.

Is flow ko yaad rakhne ka short version: **sample banao → eligibility check → do travel legs check → ETA nikaalo → best choose karo → result print karo.**

## Result dictionary ko kaise padhein?

Successful result roughly is shape ka hota hai:

- order_id: kaunsa order process hua.
- partner_id: selected delivery partner.
- pickup_minutes: current time se restaurant pickup tak ka estimate.
- eta_minutes: current time se customer delivery tak ka estimate.
- reason: assigned.

Agar valid candidate nahi milta, partner_id aur eta_minutes dono None hote hain aur reason unassigned hone ki wajah batata hai. None ka matlab missing/unknown result hai; zero ka matlab valid zero-minute estimate hota. Dono ko confuse nahi karna.

## Python syntax ke chhote meanings

- def function banata hai; jaise def estimate_eta(...) ek reusable calculation define karta hai.
- return function ka final result caller ko deta hai.
- if condition ke basis par branch choose karta hai.
- for list ke har partner par kaam karta hai.
- continue current partner ko skip karke agle partner par jaata hai.
- isinstance(value, Type) check karta hai ki value expected type ki hai.
- all(...) tab True deta hai jab group ke saare checks True hon.
- tuple jaise (eta, partner_id) do values ko ek comparison key mein rakhta hai.
- list mein value in list check karta hai ki event pehle process hua hai ya nahi.
- default argument now=0 ka matlab caller time na de to current calculation 0 se start hoti hai.

## Apni understanding check karne ke liye

Khud se yeh sawal poochkar jawab bolne ki practice karo:

1. Agar partner-to-restaurant route missing ho, code kya karega aur kyun?
2. Capacity 2 hai aur active orders 2 hain, to partner eligible kyun nahi?
3. Dono partners ka ETA same ho to winner kaise decide hota hai?
4. Duplicate event ID aane par workload dobara subtract kyun nahi hota?
5. Demo mein P-2 ka ETA 35 aur P-1 ka 36 kaise aaya?

Agar inka jawab bina file padhe apne shabdon mein de pao, to core logic tumhe samajh aa rahi hai.

