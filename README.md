# NaamAstro: astrology-based company name suggester (Django)

DOB + industry -> Moolank/Bhagyank -> naam generate -> numerology filter -> live domain check -> ranked list.

## Chalane ka tareeka
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations suggester
python manage.py migrate
python manage.py runserver
```
Poora app free hai: koi paid API ya key nahi lagti.

## Tests (Django ke bina bhi chalte hain)
```bash
python -m unittest suggester.tests.test_services -v
```

## Features
- Moolank (primary) se naam-ank filter; Bhagyank se bhi match ho to "strong" naam, score mein bonus
- Domain check 2 phase mein: pehle .com, phir top naamo ke .in/.co/.app (`NAME_SUGGESTER` settings mein badal sakte hain)
- .com taken ho to `getX.com` / `Xhq.com` option dikhata hai (agar khaali ho)
- Har naam par Instagram / X / YouTube / trademark check ke links (automatic check nahi, sirf links)
- Shortlist (is browser mein save), link copy, WhatsApp share, PDF / print
- Result URL signed hai (guess nahi hota), isliye DOB private rehti hai lekin link share ho sakta hai
- Poora free: koi paid API nahi

## Structure
- `suggester/services/numerology.py`: Chaldean number, Moolank/Bhagyank, compatibility table (**astrologer se verify karein**)
- `suggester/services/generator.py`: poori tarah rule-based naam (koi paid API nahi)
- `suggester/services/domains.py`: RDAP availability check (parallel, error par kabhi "available" nahi dikhata)
- `suggester/services/pipeline.py`: poora flow + scoring
- `suggester/static/suggester/`: CSS aur JS (shortlist, filter, loading state)

## Aage ke steps
1. Search ko Celery + Redis par shift karna (abhi request ke andar sync chalta hai)
2. Registrar API (Porkbun/GoDaddy/Namecheap) se final availability + price
3. Birth time/place se Nakshatra aur lucky letters (`pyswisseph`)
4. Hindi (Devanagari) interface
