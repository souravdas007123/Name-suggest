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

## Structure
- `suggester/services/numerology.py`: Chaldean number, Moolank/Bhagyank, compatibility table (**astrologer se verify karein**)
- `suggester/services/generator.py`: poori tarah rule-based naam (koi paid API nahi)
- `suggester/services/domains.py`: RDAP availability check (parallel, error par kabhi "available" nahi dikhata)
- `suggester/services/pipeline.py`: poora flow + scoring
- `config/settings.py` ke `NAME_SUGGESTER` dict mein TLDs, candidate count, workers

## Aage ke steps
1. Search ko Celery + Redis par shift karna (abhi request ke andar sync chalta hai)
2. Registrar API (Porkbun/GoDaddy/Namecheap) se final availability + price + buy link
3. Social handle aur trademark pre-check
4. Birth time/place se Nakshatra aur lucky letters (`pyswisseph`)
