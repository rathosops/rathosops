# Self-host dos cards (correção definitiva do "não aparece" / 429)

## Por que os cards somem (stats, top-langs, streak, trophies)

Eles são servidos por **instâncias públicas compartilhadas** no Vercel/Demolab:

| Card | Serviço público |
|------|-----------------|
| GitHub stats / Top languages | `github-readme-stats.vercel.app` |
| Streak | `streak-stats.demolab.com` |
| Trophies | `github-profile-trophy.vercel.app` |

Essas instâncias usam **uma cota compartilhada** da API do GitHub (5.000 req/h). Sob tráfego global, estouram o limite e devolvem **HTTP 429 (Too Many Requests)** → a imagem não renderiza em **qualquer navegador** (Chrome, Edge, Brave). Não é cache do seu browser e não tem a ver com o Brave Shields.

O `&cache_seconds=86400` que já foi adicionado **reduz** a frequência do erro, mas não elimina. A solução real é rodar **sua própria instância** — aí você usa a SUA cota de 5.000 req/h, que ninguém mais consome.

---

## Passo a passo (≈10 min, tudo grátis)

Você vai criar 3 instâncias no Vercel (1 clique cada) e trocar 3 domínios no `README.md`.

### Pré-requisitos
- Conta no [Vercel](https://vercel.com/signup) (faça login **com o GitHub**).
- Um **GitHub Personal Access Token (classic)** com escopo `repo` (para `count_private=true` funcionar):
  GitHub → Settings → Developer settings → Personal access tokens → **Tokens (classic)** → Generate → marque `repo` → copie o token.

### 1) github-readme-stats  (cobre *GitHub stats* + *Top languages*)
1. Abra: https://github.com/anuraghazra/github-readme-stats#deploy-on-your-own-vercel-instance
2. Clique em **Deploy** → autorize o Vercel a importar o fork.
3. Na tela de deploy, em **Environment Variables**, adicione:
   - `PAT_1` = *(o seu token classic do passo acima)*
4. Deploy. Você recebe uma URL tipo `https://github-readme-stats-SEU.vercel.app`.

### 2) github-profile-trophy  (cobre *Trophies*)
1. Abra: https://github.com/ryo-ma/github-profile-trophy#deploy-on-your-own-vercel-instance
2. **Deploy** → adicione a env var `GITHUB_TOKEN` = *(o seu token)* → Deploy.
3. URL tipo `https://github-profile-trophy-SEU.vercel.app`.

### 3) github-readme-streak-stats  (cobre *Streak*)
1. Abra: https://github.com/DenverCoder1/github-readme-streak-stats#deploy-your-own
2. **Deploy** → adicione `GH_TOKEN` = *(o seu token)* → Deploy.
3. URL tipo `https://streak-stats-SEU.vercel.app`.

---

## Trocar os domínios no README

No `README.md`, faça **find & replace** (só o domínio muda, os parâmetros ficam iguais):

| Trocar isto | Por isto |
|-------------|----------|
| `github-readme-stats.vercel.app` | `github-readme-stats-SEU.vercel.app` |
| `github-profile-trophy.vercel.app` | `github-profile-trophy-SEU.vercel.app` |
| `streak-stats.demolab.com` | `streak-stats-SEU.vercel.app` |

> Substitua `SEU` pelo sufixo real que o Vercel gerou para cada projeto.

Commit + push → os cards passam a carregar de forma estável em todos os navegadores.

---

## Observações
- O **header** (`./assets/header.svg`), o **snake** e os blocos de terminal **não dependem de Vercel** e nunca quebram por 429.
- Os cards `github-profile-summary-cards.vercel.app` e o `activity-graph` também são instâncias públicas; se quiser blindá-los, têm deploy próprio análogo — mas costumam ser mais estáveis que os 3 acima.
- O token nunca vai pro README nem pro Git: ele fica só nas Environment Variables do Vercel.
