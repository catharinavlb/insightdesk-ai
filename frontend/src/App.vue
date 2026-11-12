
<script setup>
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

// ==========================================
// FORMATAÇÃO DAS RESPOSTAS DA IA
// ==========================================

marked.setOptions({
  gfm: true,
  breaks: true
})

function formatarMarkdown(texto) {
  if (typeof texto !== 'string' || !texto) return ''

  const html = marked.parse(texto)
  return DOMPurify.sanitize(html)
}

// ==========================================
// ANÁLISE MANUAL COM IA
// ==========================================

const problema = ref('')
const resposta = ref('')
const erro = ref('')
const carregando = ref(false)

async function analisarProblema() {
  const descricao = problema.value.trim()

  if (descricao.length < 3 || carregando.value) return

  carregando.value = true
  resposta.value = ''
  erro.value = ''

  try {
    const resultado = await fetch(`${apiUrl}/agente/analisar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        problema: descricao
      })
    })

    if (!resultado.ok) {
      throw new Error(`HTTP ${resultado.status}`)
    }

    const dados = await resultado.json()

    resposta.value = dados.resposta || 'A IA não retornou uma resposta.'
  } catch {
    erro.value =
      'Não foi possível concluir a análise. Verifique o FastAPI e o Ollama.'
  } finally {
    carregando.value = false
  }
}

// ==========================================
// CADASTRO DE CHAMADOS
// ==========================================

const tituloNovo = ref('')
const descricaoNova = ref('')
const salvandoChamado = ref(false)
const mensagemCadastro = ref('')
const erroCadastro = ref('')

async function cadastrarChamado() {
  const titulo = tituloNovo.value.trim()
  const descricao = descricaoNova.value.trim()

  if (
    titulo.length < 3 ||
    descricao.length < 3 ||
    salvandoChamado.value
  ) {
    return
  }

  salvandoChamado.value = true
  mensagemCadastro.value = ''
  erroCadastro.value = ''

  try {
    const resultado = await fetch(`${apiUrl}/chamados`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        titulo,
        descricao
      })
    })

    if (!resultado.ok) {
      throw new Error(`HTTP ${resultado.status}`)
    }

    const chamadoCriado = await resultado.json()

    mensagemCadastro.value =
      `Chamado #${chamadoCriado.id} cadastrado com sucesso!`

    tituloNovo.value = ''
    descricaoNova.value = ''

    await carregarChamados()
  } catch {
    erroCadastro.value =
      'Não foi possível cadastrar o chamado. Verifique a conexão com a API.'
  } finally {
    salvandoChamado.value = false
  }
}

// ==========================================
// LISTAGEM E INDICADORES
// ==========================================

const chamados = ref([])
const carregandoChamados = ref(false)
const erroChamados = ref('')

const totalChamados = computed(() => chamados.value.length)

const chamadosAbertos = computed(() =>
  chamados.value.filter(
    chamado => chamado.status?.toLowerCase() === 'aberto'
  ).length
)

const chamadosEmAndamento = computed(() =>
  chamados.value.filter(
    chamado => chamado.status?.toLowerCase() === 'em andamento'
  ).length
)

const chamadosResolvidos = computed(() =>
  chamados.value.filter(
    chamado => chamado.status?.toLowerCase() === 'resolvido'
  ).length
)

async function carregarChamados() {
  carregandoChamados.value = true
  erroChamados.value = ''

  try {
    const resultado = await fetch(`${apiUrl}/chamados`)

    if (!resultado.ok) {
      throw new Error(`HTTP ${resultado.status}`)
    }

    const dados = await resultado.json()

    if (!Array.isArray(dados)) {
      throw new Error('Formato de dados inesperado')
    }

    chamados.value = dados
  } catch {
    erroChamados.value =
      'Não foi possível carregar os chamados. Confira se o FastAPI está funcionando.'
  } finally {
    carregandoChamados.value = false
  }
}

// ==========================================
// ATUALIZAÇÃO DE STATUS
// ==========================================

const atualizandoStatus = ref(null)
const erroStatus = ref('')

async function alterarStatus(chamado, novoStatus) {
  if (
    chamado.status === novoStatus ||
    atualizandoStatus.value !== null
  ) {
    return
  }

  atualizandoStatus.value = chamado.id
  erroStatus.value = ''

  try {
    const resultado = await fetch(
      `${apiUrl}/chamados/${chamado.id}/status`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: novoStatus
        })
      }
    )

    if (!resultado.ok) {
      throw new Error(`HTTP ${resultado.status}`)
    }

    const chamadoAtualizado = await resultado.json()

    chamados.value = chamados.value.map(item =>
      item.id === chamado.id
        ? { ...item, status: chamadoAtualizado.status }
        : item
    )
  } catch {
    erroStatus.value =
      `Não foi possível atualizar o chamado #${chamado.id}.`

    await carregarChamados()
  } finally {
    atualizandoStatus.value = null
  }
}

// ==========================================
// ANÁLISE INDIVIDUAL DE CHAMADOS COM IA
// ==========================================

const chamadoAnalisando = ref(null)
const resultadoAnaliseChamado = ref(null)
const erroAnaliseChamado = ref('')

async function analisarChamado(chamado) {
  if (chamadoAnalisando.value !== null) return

  chamadoAnalisando.value = chamado.id
  resultadoAnaliseChamado.value = null
  erroAnaliseChamado.value = ''

  try {
    const resultado = await fetch(`${apiUrl}/agente/analisar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        problema: `${chamado.titulo}\n${chamado.descricao}`
      })
    })

    if (!resultado.ok) {
      throw new Error(`HTTP ${resultado.status}`)
    }

    const dados = await resultado.json()

    resultadoAnaliseChamado.value = {
      id: chamado.id,
      titulo: chamado.titulo,
      resposta: dados.resposta || 'A IA não retornou uma resposta.'
    }
  } catch {
    erroAnaliseChamado.value =
      `Não foi possível analisar o chamado #${chamado.id}. Verifique o agente de IA.`
  } finally {
    chamadoAnalisando.value = null
  }
}

// ==========================================
// INICIALIZAÇÃO
// ==========================================

onMounted(carregarChamados)
</script>

<template>
  <div class="aplicativo">

    <!-- BARRA SUPERIOR -->
    <header class="barra">
      <div class="barra-conteudo">
        <span class="marca" aria-hidden="true">ID</span>
        <span>InsightDesk IA</span>
      </div>
    </header>

    <main class="pagina">

      <!-- INTRODUÇÃO -->
      <div class="introducao">
        <h1>Central de suporte</h1>

        <p>
          Cadastre chamados, acompanhe problemas técnicos
          e consulte orientações com inteligência artificial.
        </p>
      </div>

      <!-- CADASTRO -->
      <section class="painel secao-cadastro">
        <h2>Cadastrar novo chamado</h2>

        <form @submit.prevent="cadastrarChamado">

          <label for="titulo-novo">
            Título do chamado
          </label>

          <input
            id="titulo-novo"
            v-model="tituloNovo"
            type="text"
            minlength="3"
            maxlength="150"
            placeholder="Ex.: Erro ao acessar o sistema"
            :disabled="salvandoChamado"
            required
          />

          <label for="descricao-nova">
            Descrição do problema
          </label>

          <textarea
            id="descricao-nova"
            v-model="descricaoNova"
            rows="4"
            minlength="3"
            placeholder="Descreva o erro e quando ele acontece."
            :disabled="salvandoChamado"
            required
          ></textarea>

          <button
            class="botao-principal"
            type="submit"
            :disabled="
              salvandoChamado ||
              tituloNovo.trim().length < 3 ||
              descricaoNova.trim().length < 3
            "
          >
            {{
              salvandoChamado
                ? 'Salvando...'
                : 'Cadastrar chamado'
            }}
          </button>
        </form>

        <p
          v-if="mensagemCadastro"
          class="sucesso mensagem-formulario"
          role="status"
        >
          {{ mensagemCadastro }}
        </p>

        <p
          v-if="erroCadastro"
          class="erro mensagem-formulario"
          role="alert"
        >
          {{ erroCadastro }}
        </p>
      </section>

      <!-- ANÁLISE MANUAL -->
      <section class="secao-ia">

        <div class="cabecalho-secao">
          <h2>Análise com IA</h2>

          <p>
            Consulte a base de soluções para receber uma orientação.
          </p>
        </div>

        <div class="paineis">

          <section class="painel">
            <h2>Descrever problema</h2>

            <form @submit.prevent="analisarProblema">

              <label for="problema">
                Descrição do problema
              </label>

              <textarea
                id="problema"
                v-model="problema"
                rows="6"
                minlength="3"
                placeholder="Informe o sistema afetado e a mensagem de erro."
                :disabled="carregando"
                required
              ></textarea>

              <button
                class="botao-principal"
                type="submit"
                :disabled="
                  carregando ||
                  problema.trim().length < 3
                "
              >
                {{
                  carregando
                    ? 'Analisando...'
                    : 'Analisar com IA'
                }}
              </button>
            </form>
          </section>

          <section class="painel painel-resposta">
            <h2>Orientação do agente</h2>

            <div role="status">

              <p
                v-if="carregando"
                class="estado"
              >
                Consultando a base de soluções...
              </p>

              <div
                v-else-if="resposta"
                class="resposta conteudo-markdown"
                v-html="formatarMarkdown(resposta)"
              ></div>

              <p
                v-else-if="!erro"
                class="estado"
              >
                A orientação aparece aqui após a análise.
              </p>
            </div>

            <p
              v-if="erro"
              class="erro"
              role="alert"
            >
              {{ erro }}
            </p>
          </section>
        </div>
      </section>

      <!-- PAINEL DE CHAMADOS -->
      <section class="secao-chamados">

        <div class="cabecalho-chamados">

          <div>
            <h2>Painel de chamados</h2>

            <p>
              Acompanhe os problemas registrados no sistema.
            </p>
          </div>

          <button
            class="botao-atualizar"
            type="button"
            :disabled="carregandoChamados"
            @click="carregarChamados"
          >
            {{
              carregandoChamados
                ? 'Atualizando...'
                : 'Atualizar'
            }}
          </button>
        </div>

        <!-- INDICADORES -->
        <div class="indicadores">

          <div class="indicador">
            <span>Total de chamados</span>
            <strong>{{ totalChamados }}</strong>
          </div>

          <div class="indicador">
            <span>Chamados abertos</span>
            <strong>{{ chamadosAbertos }}</strong>
          </div>

          <div class="indicador">
            <span>Em andamento</span>
            <strong>{{ chamadosEmAndamento }}</strong>
          </div>

          <div class="indicador">
            <span>Resolvidos</span>
            <strong>{{ chamadosResolvidos }}</strong>
          </div>
        </div>

        <p
          v-if="erroStatus"
          class="erro erro-status"
          role="alert"
        >
          {{ erroStatus }}
        </p>

        <!-- TABELA -->
        <div class="painel tabela-painel">

          <p
            v-if="carregandoChamados"
            class="estado"
          >
            Carregando chamados...
          </p>

          <p
            v-else-if="erroChamados"
            class="erro"
            role="alert"
          >
            {{ erroChamados }}
          </p>

          <p
            v-else-if="chamados.length === 0"
            class="estado"
          >
            Nenhum chamado cadastrado.
          </p>

          <div v-else class="tabela-rolagem">

            <table class="tabela-chamados">

              <thead>
                <tr>
                  <th>ID</th>
                  <th>Título</th>
                  <th>Descrição</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>

              <tbody>

                <tr
                  v-for="chamado in chamados"
                  :key="chamado.id"
                >

                  <td>#{{ chamado.id }}</td>

                  <td>{{ chamado.titulo }}</td>

                  <td>{{ chamado.descricao }}</td>

                  <!-- STATUS -->
                  <td>
                    <select
                      :key="`${chamado.id}-${chamado.status}`"
                      class="seletor-status"
                      :class="{
                        'seletor-aberto':
                          chamado.status === 'aberto',
                        'seletor-andamento':
                          chamado.status === 'em andamento',
                        'seletor-resolvido':
                          chamado.status === 'resolvido'
                      }"
                      :value="chamado.status"
                      :disabled="atualizandoStatus !== null"
                      :aria-label="`Status do chamado ${chamado.id}`"
                      @change="
                        alterarStatus(
                          chamado,
                          $event.target.value
                        )
                      "
                    >
                      <option value="aberto">
                        Aberto
                      </option>

                      <option value="em andamento">
                        Em andamento
                      </option>

                      <option value="resolvido">
                        Resolvido
                      </option>
                    </select>

                    <span
                      v-if="atualizandoStatus === chamado.id"
                      class="texto-atualizando"
                    >
                      Salvando...
                    </span>
                  </td>

                  <!-- BOTÃO DE ANÁLISE -->
                  <td>
                    <button
                      type="button"
                      class="botao-analisar-chamado"
                      :disabled="chamadoAnalisando !== null"
                      @click="analisarChamado(chamado)"
                    >
                      {{
                        chamadoAnalisando === chamado.id
                          ? 'Analisando...'
                          : 'Analisar com IA'
                      }}
                    </button>
                  </td>

                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- RESULTADO DA IA -->
        <div
          v-if="resultadoAnaliseChamado"
          class="painel resultado-chamado"
          role="status"
        >
          <h3>
            Análise do chamado
            #{{ resultadoAnaliseChamado.id }}
          </h3>

          <p class="titulo-chamado-analisado">
            {{ resultadoAnaliseChamado.titulo }}
          </p>

          <h4>
            Solução sugerida pela IA
          </h4>

          <div
            class="resposta conteudo-markdown"
            v-html="
              formatarMarkdown(
                resultadoAnaliseChamado.resposta
              )
            "
          ></div>
        </div>

        <p
          v-if="erroAnaliseChamado"
          class="erro erro-analise-chamado"
          role="alert"
        >
          {{ erroAnaliseChamado }}
        </p>

      </section>
    </main>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:global(html) {
  color-scheme: light;
  background: #e5edf8;
}

:global(body) {
  display: block;
  margin: 0;
}

:global(#app) {
  display: block;
  width: 100%;
  max-width: none;
  min-height: 100vh;
  margin: 0;
  padding: 0;
}

.aplicativo,
.aplicativo * {
  box-sizing: border-box;
}

.aplicativo {
  min-height: 100vh;
  background:
    radial-gradient(
      ellipse at top right,
      #d6e2fb,
      transparent 55%
    ),
    #e5edf8;
  color: #182642;
  font-family: "Inter", "Segoe UI", sans-serif;
  line-height: 1.55;
  text-align: left;
}

.barra {
  background: #111d38;
  color: #fff;
}

.barra-conteudo,
.pagina {
  width: min(calc(100% - 40px), 1120px);
  margin-inline: auto;
}

.barra-conteudo {
  display: flex;
  min-height: 68px;
  align-items: center;
  gap: 12px;
  font-family: "Space Grotesk", "Segoe UI", sans-serif;
  font-weight: 700;
}

.marca {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  border-radius: 9px;
  background: #dbe5ff;
  color: #233b81;
  font-size: 13px;
}

.pagina {
  padding-block: clamp(32px, 6vw, 72px);
}

.introducao {
  margin-bottom: 28px;
}

.aplicativo .introducao h1,
.aplicativo .painel h2 {
  color: #182642;
  font-family: "Space Grotesk", "Segoe UI", sans-serif;
  font-weight: 700;
}

.aplicativo .introducao h1 {
  margin: 0;
  font-size: clamp(30px, 5vw, 44px);
  line-height: 1.15;
  letter-spacing: -0.035em;
}

.introducao p {
  margin: 10px 0 0;
  color: #465773;
}

.painel {
  padding: clamp(18px, 3vw, 28px);
  border: 1px solid #cbd7ea;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 8px 24px rgb(24 38 66 / 7%);
}

.aplicativo .painel h2 {
  margin: 0 0 20px;
  font-size: 22px;
  line-height: 1.3;
}

.secao-cadastro,
.secao-ia {
  margin-bottom: 44px;
}

.cabecalho-secao {
  margin-bottom: 20px;
}

.aplicativo .cabecalho-secao h2 {
  margin: 0;
  color: #182642;
  font-family: "Space Grotesk", "Segoe UI", sans-serif;
  font-size: 26px;
  font-weight: 700;
}

.cabecalho-secao p {
  margin: 6px 0 0;
  color: #465773;
}

.paineis {
  display: grid;
  grid-template-columns:
    minmax(0, 1.15fr)
    minmax(0, 1fr);
  gap: 20px;
}

.painel-resposta {
  background: #f4f7ff;
}

form {
  display: grid;
  gap: 10px;
}

label {
  color: #243654;
  font-size: 14px;
  font-weight: 600;
}

input,
textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #8fa2c2;
  border-radius: 9px;
  background: #f9fbff;
  color: #182642;
  font: inherit;
}

textarea {
  min-height: 120px;
  resize: vertical;
}

input::placeholder,
textarea::placeholder {
  color: #59687c;
}

input:focus-visible,
textarea:focus-visible,
button:focus-visible,
select:focus-visible {
  outline: 3px solid #3c50c4;
  outline-offset: 3px;
}

.botao-principal {
  justify-self: start;
  min-height: 44px;
  margin-top: 6px;
  padding: 10px 16px;
  border: 1px solid transparent;
  border-radius: 9px;
  background: #3346b5;
  color: #fff;
  font: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.botao-principal:hover:not(:disabled) {
  background: #293a9c;
}

.botao-principal:disabled {
  background: #e1e7f5;
  color: #465578;
  cursor: default;
}

.estado,
.resposta,
.erro,
.sucesso {
  margin: 0;
  padding: 16px;
  border-radius: 9px;
  overflow-wrap: anywhere;
}

.estado {
  border: 1px dashed #9dadce;
  background: #eaf0fc;
  color: #3c4e70;
}

.resposta {
  border-left: 3px solid #3c50c4;
  background: #e7edff;
  color: #182642;
}

.erro {
  background: #fff1ef;
  color: #9b251b;
}

.sucesso {
  background: #e7f6ed;
  color: #17683a;
}

.mensagem-formulario {
  margin-top: 16px;
}

/* PAINEL DE CHAMADOS */

.secao-chamados {
  margin-top: 44px;
}

.cabecalho-chamados {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.cabecalho-chamados h2 {
  margin: 0;
  color: #182642;
  font-family: "Space Grotesk", "Segoe UI", sans-serif;
  font-size: 26px;
}

.cabecalho-chamados p {
  margin: 6px 0 0;
  color: #465773;
}

.botao-atualizar {
  padding: 10px 18px;
  border: 1px solid #aab9d5;
  border-radius: 9px;
  background: white;
  color: #243654;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.botao-atualizar:hover:not(:disabled) {
  background: #f4f7ff;
}

.botao-atualizar:disabled {
  opacity: 0.6;
  cursor: default;
}

/* INDICADORES */

.indicadores {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.indicador {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px;
  border: 1px solid #cbd7ea;
  border-radius: 16px;
  background: white;
}

.indicador span {
  color: #465773;
  font-size: 14px;
}

.indicador strong {
  color: #182642;
  font-size: 36px;
}

/* TABELA */

.tabela-painel {
  padding: 0;
  overflow: hidden;
}

.tabela-painel > .estado,
.tabela-painel > .erro {
  margin: 20px;
}

.tabela-rolagem {
  overflow-x: auto;
}

.tabela-chamados {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.tabela-chamados th,
.tabela-chamados td {
  padding: 16px;
  border-bottom: 1px solid #e1e7f2;
  vertical-align: middle;
}

.tabela-chamados th {
  background: #f4f7ff;
  color: #465773;
  font-size: 13px;
}

.tabela-chamados td {
  font-size: 14px;
  overflow-wrap: anywhere;
}

/* SELETOR DE STATUS */

.seletor-status {
  min-width: 145px;
  padding: 9px 12px;
  border: 1px solid #aab9d5;
  border-radius: 9px;
  background: #f9fbff;
  color: #182642;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.seletor-aberto {
  background: #fff1d6;
  color: #805500;
  border-color: #ead29b;
}

.seletor-andamento {
  background: #e7edff;
  color: #263e9a;
  border-color: #b7c5f2;
}

.seletor-resolvido {
  background: #e7f6ed;
  color: #17683a;
  border-color: #a7d8b9;
}

.seletor-status:disabled {
  opacity: 0.6;
  cursor: wait;
}

.texto-atualizando {
  display: block;
  margin-top: 5px;
  color: #465773;
  font-size: 12px;
}

.erro-status {
  margin-bottom: 16px;
}

/* BOTÃO DE ANÁLISE */

.botao-analisar-chamado {
  min-width: 135px;
  padding: 9px 12px;
  border: 1px solid #3346b5;
  border-radius: 9px;
  background: #3346b5;
  color: white;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.botao-analisar-chamado:hover:not(:disabled) {
  background: #293a9c;
}

.botao-analisar-chamado:disabled {
  opacity: 0.6;
  cursor: wait;
}

.resultado-chamado {
  margin-top: 20px;
}

.resultado-chamado h3 {
  margin: 0 0 8px;
  font-size: 20px;
}

.aplicativo .resultado-chamado h4 {
  display: block;
  width: 100%;
  margin: 20px 0 10px;
  padding: 0;
  color: #182642;
  font-size: 15px;
  font-weight: 700;
  text-align: left;
  white-space: normal;
  overflow-wrap: break-word;
}

.titulo-chamado-analisado {
  color: #465773;
}

.erro-analise-chamado {
  margin-top: 16px;
}

/* FORMATAÇÃO MARKDOWN DA IA */

.conteudo-markdown {
  line-height: 1.7;
  white-space: normal;
}

.conteudo-markdown :deep(p) {
  margin: 0 0 12px;
}

.conteudo-markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.conteudo-markdown :deep(ol),
.conteudo-markdown :deep(ul) {
  margin: 12px 0;
  padding-left: 24px;
}

.conteudo-markdown :deep(li) {
  margin-bottom: 8px;
}

.conteudo-markdown :deep(strong) {
  font-weight: 700;
}

.conteudo-markdown :deep(h1),
.conteudo-markdown :deep(h2),
.conteudo-markdown :deep(h3) {
  margin: 16px 0 10px;
  color: #182642;
  font-family: "Space Grotesk", "Segoe UI", sans-serif;
}

.conteudo-markdown :deep(code) {
  padding: 2px 5px;
  border-radius: 4px;
  background: #d7e1fa;
  overflow-wrap: anywhere;
}

.conteudo-markdown :deep(pre) {
  padding: 14px;
  border-radius: 8px;
  background: #182642;
  color: #fff;
  overflow-x: auto;
}

.conteudo-markdown :deep(pre code) {
  padding: 0;
  background: transparent;
  color: inherit;
}

.conteudo-markdown :deep(a) {
  color: #263e9a;
  text-decoration: underline;
  overflow-wrap: anywhere;
}

/* RESPONSIVIDADE */

@media (max-width: 900px) {
  .indicadores {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .paineis {
    grid-template-columns: 1fr;
  }

  .cabecalho-chamados {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .indicadores {
    grid-template-columns: 1fr;
  }
}
</style>
