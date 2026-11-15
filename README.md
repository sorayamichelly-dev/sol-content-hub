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
- Site estático: `index.html`, `css/`, `js/`, `manifest.webmanifest`, `sw.js`.
- **Contas:** login com e-mail e senha pelo Supabase (projeto `sol-content-hub`). Só cria conta quem foi convidada. A primeira conta criada vira administradora e libera os convites em **Ajustes → Convites**.
- **Dados:** cada pessoa só vê os próprios dados (regras de segurança no banco). Uma cópia fica no aparelho para abrir rápido e funcionar sem internet; o que mudar offline é enviado quando a conexão voltar.
- **IA:** cada pessoa cola a própria chave da Anthropic em Ajustes. A chave fica só no aparelho, não vai para o servidor.

## Publicar
Ative o GitHub Pages no repositório (Settings → Pages → branch) e abra o endereço no celular. Depois é só usar "Adicionar à Tela de Início".
