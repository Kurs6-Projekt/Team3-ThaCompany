# Säkerhetsgranskning av company-website

**Senast uppdaterad:** 2026-10-05
**Omfattning:** Flask-applikation, beroenden, container, Kubernetes, GitHub Actions och körande labbmiljö

## Sammanfattning

De tidigare applikationsfynden SQL-injektion, IDOR, SSTI, förutsägbar Flask-nyckel och saknat CSRF-skydd är åtgärdade. Den aktuella Python-koden klarade tester och automatiska säkerhetskontroller utan nya kodfynd.

De största kvarvarande riskerna finns i leverans- och driftkedjan. `main` saknar branch protection samtidigt som deployment-workflowen har tillgång till Headscale, Kubernetes och GitHub Container Registry. Kubernetes använder dessutom en långlivad deploy-token med bred behörighet i `default`-namespace. Tillsammans innebär det att ett komprometterat GitHub-konto med pushrättighet kan leda till kontroll över applikationens namespace.

SBOM-scannern ger värdefull övervakning, men kör ett installationsskript direkt från en extern `main`-branch och verifierar inte SBOM-attesteringens identitet innan den skannas. Applikationscontainern kör som root, får en onödig Kubernetes-token och saknar flera grundläggande skydd.

## Genomförd verifiering

Granskningen utfördes mot senaste `main` och den auktoriserade Team 3-labbmiljön.

| Kontroll | Resultat |
|---|---|
| Pytest | 20 tester godkända |
| pip-audit | Inga kända sårbara Python-beroenden |
| Bandit | Inga Python-kodfynd |
| Semgrep | 0 fynd från 208 regler |
| Checkov | 42 Kubernetes-/containerfynd, sammanförda till riskerna nedan |
| Dependabot | Inga öppna alerts |
| Branch protection | Saknas på `main` |
| Körande container | Kör som `root` och har service-account-token monterad |
| Sessionscookie | `HttpOnly` och `SameSite=Lax`, men saknar `Secure` |

Inga produktionsuppgifter, databasinnehåll eller secrets ändrades under verifieringen.

## Tidigare registrerade säkerhetsärenden

| Issue | Fynd | Aktuell status |
|---|---|---|
| [#1](https://github.com/Kurs6-Projekt/Team3-ThaCompany/issues/1) | SQL-injektion i inloggningen | Åtgärdad med parametriserad fråga och lösenordskontroll |
| [#2](https://github.com/Kurs6-Projekt/Team3-ThaCompany/issues/2) | IDOR för användarprofiler | Åtgärdad med ägarskapskontroll |
| [#3](https://github.com/Kurs6-Projekt/Team3-ThaCompany/issues/3) | CTF-flagga i Git-historik | Issue stängd; objektet finns kvar i nåbar historik |
| [#4](https://github.com/Kurs6-Projekt/Team3-ThaCompany/issues/4) | CTF-flagga på remote-branch | Åtgärdad; den berörda remote-branchen finns inte längre |
| [#16](https://github.com/Kurs6-Projekt/Team3-ThaCompany/issues/16) | Förutsägbar Flask `SECRET_KEY` | Åtgärdad med GitHub- och Kubernetes-secret |
| [#17](https://github.com/Kurs6-Projekt/Team3-ThaCompany/issues/17) | Saknat CSRF-skydd | Åtgärdad med Flask-WTF och CSRF-token |

Historiska CTF-flaggor ska betraktas som övningsdata. Om samma metod någon gång exponerar en riktig hemlighet måste hemligheten roteras även om Git-historiken senare rensas.

## Kvarvarande fynd

### Fynd 1: Oskyddad main-branch och långlivad Kubernetes-token

**Allvarlighetsgrad:** Kritisk
**Berörda filer:** `.github/workflows/deploy.yml`, `k8s/github-permissions.yaml`, `scripts/generate-kubeconfig.sh`
**Status:** Öppen

En push till `main` startar deployment-workflowen. `main` saknar branch protection och workflowen får tillgång till `HEADSCALE_API_KEY`, `KUBECONFIG`, `APP_SECRET_KEY`, GHCR och GitHub OIDC.

Kubeconfig-filen använder en manuellt skapad `kubernetes.io/service-account-token`. Den körande tokenen skapades 2026-09-21 och är fortfarande giltig. Följande behörigheter verifierades för `github-deployer` i `default`-namespace:

```text
get secrets:    yes
delete secrets: yes
create pods:    yes
```

Kontot kan även skapa, uppdatera och radera deployments, services, PVC:er och ingress-resurser. En angripare som får tillgång till workflow-secrets kan därför läsa applikationshemligheter och köra egna workloads i namespace.

**Rekommenderad åtgärd:**

- Aktivera branch protection med obligatorisk PR, godkända tester och granskare.
- Använd ett GitHub Environment med godkännande för deployment.
- Ersätt den permanenta Kubernetes-tokenen med kortlivad autentisering.
- Ta bort `list`, `watch` och `delete` för secrets och övriga verbs som deploymenten inte behöver.
- Förkonfigurera applikationssecreten utanför den vanliga deployrollen.

### Fynd 2: SBOM-scannern kör extern kod från en rörlig branch

**Allvarlighetsgrad:** Hög
**Berörd fil:** `k8s/sbom-scanner/scanner-cronjob.yaml`
**Status:** Öppen

CronJoben installerar Trivy vid varje körning med följande mönster:

```bash
curl https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh
```

Innehållet i den externa `main`-branchen kan förändras utan någon ändring i Team 3-repot. Ett komprometterat upstream-repo eller installationsskript ger kodkörning i scanner-podden. Podden kör som root och får Discord-webhooken som miljövariabel.

**Rekommenderad åtgärd:** Bygg en egen scanner-image med bestämda versioner av Trivy, Cosign, curl och jq. Signera imagen och referera till den med digest.

### Fynd 3: Sårbarhetskontrollen sker efter deployment

**Allvarlighetsgrad:** Hög
**Berörda filer:** `.github/workflows/deploy.yml`, `k8s/sbom-scanner/scanner-cronjob.yaml`
**Status:** Öppen

Deploy-workflowen bygger, signerar och driftsätter imagen. CronJoben skannar den körande imagen senare enligt ett dagligt schema. En image med en känd High/Critical-sårbarhet kan därför vara aktiv fram till nästa lyckade scannerkörning. Om CronJoben misslyckas skickas inget särskilt driftlarm till Discord.

**Rekommenderad åtgärd:** Kör Trivy mot imagen eller den genererade SBOM-filen i CI och stoppa deployment vid överenskommen nivå. Behåll CronJoben för återkommande kontroll och lägg till larm för misslyckade scannerjobb.

### Fynd 4: SBOM-attesteringen verifieras inte

**Allvarlighetsgrad:** Medel
**Berörd fil:** `k8s/sbom-scanner/scanner-cronjob.yaml`
**Status:** Öppen

Scannern använder `cosign download attestation`, avkodar innehållet och skickar det direkt till Trivy. Kommandot kontrollerar inte att attesteringen signerades av Team 3:s godkända GitHub-workflow. En felaktig eller manipulerad attestation kan därmed ge missvisande scannerresultat.

**Rekommenderad åtgärd:** Använd `cosign verify-attestation` med GitHubs OIDC issuer och den exakta workflow-identiteten. Skanna endast predicate-data från en godkänd verifiering.

### Fynd 5: Applikationscontainern kör som root och har onödig API-token

**Allvarlighetsgrad:** Medel
**Berörda filer:** `Dockerfile`, `k8s/deployment.yaml`
**Status:** Öppen

Den körande applikationscontainern verifierades med följande resultat:

```text
uid=0(root) gid=0(root)
service-account-token-mounted
```

Applikationen behöver inte Kubernetes API. Default-kontot har begränsad åtkomst, men tokenen ger API-discovery och ökar angreppsytan. Deploymenten saknar även seccomp-profil, capability-begränsning, skydd mot privilege escalation och resursgränser.

**Rekommenderad åtgärd:**

```yaml
spec:
  automountServiceAccountToken: false
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: web
      securityContext:
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]
```

Skapa dessutom en användare med högt UID i Docker-imagen och ange CPU-/minnesgränser.

### Fynd 6: Okrypterad HTTP och sessionscookie utan Secure

**Allvarlighetsgrad:** Medel
**Berörda filer:** `k8s/ingress.yaml`, `k8s/deployment.yaml`, `src/company_website/config.py`
**Status:** Öppen

Applikationen exponeras via HTTP. Live-svaret satte sessionscookien med `HttpOnly` och `SameSite=Lax`, men utan attributet `Secure`. Deploymenten sätter uttryckligen `SESSION_COOKIE_SECURE=false`.

**Rekommenderad åtgärd:** Aktivera TLS på ingressen och sätt `SESSION_COOKIE_SECURE=true`. Lägg även till HSTS när all åtkomst använder HTTPS.

### Fynd 7: NetworkPolicy och resursgränser saknas

**Allvarlighetsgrad:** Medel
**Berörda filer:** `k8s/deployment.yaml`, saknad NetworkPolicy
**Status:** Öppen

Klustret har inga NetworkPolicies. En komprometterad pod kan därför försöka nå andra pods, Kubernetes-tjänster och VPC-resurser. Det saknas även LimitRange och ResourceQuota, och containrarna saknar egna requests/limits. Detta ökar risken för lateral rörelse och resursbaserad överbelastning.

**Rekommenderad åtgärd:** Inför default-deny i applikationens namespace och tillåt endast trafik från ingress-nginx samt dokumenterad utgående trafik. Ange rimliga CPU- och minnesgränser.

### Fynd 8: GitHub Actions är inte låsta till commit-SHA

**Allvarlighetsgrad:** Medel
**Berörda filer:** `.github/workflows/deploy.yml`, `.github/workflows/tests.yml`
**Status:** Öppen

Externa Actions refereras med flyttbara versionstaggar som `@v4`, `@v6` och `@v7`. Repot tillåter alla GitHub Actions och kräver inte SHA-pinning. En komprometterad eller flyttad tagg kan påverka bygget och få tillgång till jobbets tokens och secrets.

**Rekommenderad åtgärd:** Lås varje extern Action till fullständig commit-SHA och använd Dependabot för kontrollerade uppdateringar. Begränsa tillåtna Actions i repository-inställningarna.

### Fynd 9: Inloggningen saknar rate limiting och använder delat labbkonto

**Allvarlighetsgrad:** Låg/medel
**Berörd kod:** `src/company_website/auth.py`
**Status:** Öppen

Inloggningen saknar begränsning av upprepade försök. Det dokumenterade kontot `dev` delas av flera användare, vilket försämrar spårbarheten. I den nuvarande Tailnet-avgränsade labbmiljön är risken lägre än för en publik tjänst.

**Rekommenderad åtgärd:** Skapa personliga konton, inför rate limiting och logga misslyckade inloggningsförsök utan att logga lösenord.

### Fynd 10: Säkerhetsheaders saknas

**Allvarlighetsgrad:** Låg
**Berörda komponenter:** Flask och ingress-nginx
**Status:** Öppen

Live-svaren saknar Content Security Policy, `X-Content-Type-Options`, frame-skydd och `Referrer-Policy`.

**Rekommenderad åtgärd:** Sätt en anpassad CSP och övriga headers i ingress-nginx eller med Flask-Talisman. Verifiera att CSP:n tillåter applikationens befintliga CSS och JavaScript innan den görs blockerande.

## Prioriterad åtgärdsordning

1. Skydda `main`, inför deployment-godkännande och ersätt den långlivade Kubernetes-tokenen.
2. Flytta sårbarhetsscanningen till CI och bygg en versionslåst scanner-image.
3. Verifiera SBOM-attesteringen kryptografiskt.
4. Kör applikationen utan root och utan service-account-token.
5. Inför TLS, säkra sessionscookies och NetworkPolicy.
6. Lås GitHub Actions till SHA och lägg till resursgränser.
7. Inför rate limiting och säkerhetsheaders.

## Avgränsning för framtida pentestmiljö

Om en sårbar och en patchad version ska köras parallellt bör de använda separata namespaces, databaser, service accounts och hostnames. Den sårbara versionen ska endast innehålla avsiktliga applikationssårbarheter. Infrastrukturens secrets, Kubernetes API och molnidentiteter ska inte vara åtkomliga från pentestcontainern.
