# Sol Content Hub

Site que vira app (PWA) para organizar o trabalho de criadora UGC.

## O que tem
- **Agenda**: calendário que junta compromissos, prazos de entrega, pagamentos, chegada de produtos e ideias agendadas.
- **Marcas**: uma pasta por marca aprovada, com origem (direto ou plataforma), valor, data de recebimento, permuta ou afiliado, código de rastreio, entregas, briefing, roteiros, e-mails e vídeos.
- **Briefing**: cole o texto ou um print e a IA analisa o que a marca pede.
- **Roteiros**: ganchos e roteiro gerados pela IA, com "Gerar novo" e ajuste por texto.
- **Ideias**: banco de ideias de posts, com data e status.
- **Propostas**: print do que a marca busca, e a IA cria a abordagem (direct, e-mail e ideias).
- **Edição de vídeo**: checklist de edição, links e pedido pronto para colar no Descript, com legenda e hashtags.
- **Portfólio**: marcas, faixa de logos e pedido de atualização do site e do PDF.

## Como funciona
- Site estático, sem servidor: `index.html`, `css/`, `js/`, `manifest.webmanifest`, `sw.js`.
- Os dados ficam salvos no próprio aparelho (IndexedDB). Use **Ajustes → Baixar backup** para guardar uma cópia ou passar para outro aparelho.
- A IA usa a API da Anthropic (Claude). A chave é colada em **Ajustes** e fica salva só no aparelho.
- A versão antiga do hub está em `legado/guia-crescimento.html`.

## Publicar
Ative o GitHub Pages no repositório (Settings → Pages → branch) e abra o endereço no celular. Depois é só usar "Adicionar à Tela de Início".
