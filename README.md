# PaceAI — Deploy su Railway

## Struttura
```
paceai/
├── server.py          # Backend Flask + Garmin
├── requirements.txt   # Dipendenze Python
├── Procfile           # Comando avvio Railway
├── railway.json       # Config Railway
└── static/
    └── index.html     # App mobile
```

## Deploy in 5 minuti

### 1. Carica su GitHub
1. Vai su github.com → New repository → nome "paceai" → Create
2. Carica tutti i file (drag & drop nella pagina del repo)

### 2. Deploy su Railway
1. Vai su railway.app → Login con GitHub
2. New Project → Deploy from GitHub repo → seleziona "paceai"
3. Railway fa tutto automaticamente (rileva Python, installa deps)
4. Dopo 1-2 minuti: Settings → Networking → Generate Domain
5. Copia il link (es. paceai-production.up.railway.app)

### 3. Apri dal tuo iPhone
- Vai sul link Railway dal Safari
- Tocca Share → "Aggiungi a schermata Home"
- Hai l'app installata come app nativa!

## Uso
1. Apri l'app → inserisci email e password Garmin Connect
2. I dati vengono caricati (Body Battery, HRV, sonno, run recenti...)
3. Vai su "Coach" → chiedi consigli o genera un piano
4. Il Coach usa i tuoi dati reali Garmin per rispondere

## Note
- Le credenziali Garmin sono usate solo per la sessione corrente
- Il piano gratuito Railway è sufficiente (500h/mese)
- Se la sessione scade, basta rifare il login
