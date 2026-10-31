# Four Seasons — estúdio 4 do Vivaldi

Criação musical local em **4 estações**, ligada às playlists do **Apple Music** e à IA no **M4 (Ollama)**.

## Estações
| Estação | Fase | O que faz |
|---------|------|-----------|
| **Primavera** | Pré-produção | Conceito, mood, tom/BPM, DNA da playlist Apple Music |
| **Verão** | Produção | Cantarolar, rack de instrumentos (+), gerar camadas |
| **Outono** | Arranjo | Chat para ajustar camadas (“inspire-se em X / artista Y”) |
| **Inverno** | Pós-produção | Mix notes, **CIFRA** + **partitura ABC** por instrumento, export |

## Referências Apple Music
Abra uma playlist no estúdio Apple Music → Four Seasons lê a sessão e usa artistas/gêneros/faixas como DNA estético (sem copiar melodias).

## Instrumentos
Botão **+ Adicionar**: escolha piano, voz, baixo, bateria, cordas, etc. Cada camada ganha notas, acordes, cifra e ABC.

## Cantarolar
Grave/envie áudio no Verão. WAV 16-bit recebe estimativa de tom local; a IA usa o take como seed melódico.

## Saídas
Arquivos em `four_seasons_out/`:
- projeto JSON
- `*_scores/` com `*_cifra.txt` e `*_partitura.abc` por instrumento

## Limite honesto
Não é um DAW completo nem gerador de áudio wavetable cloud. É um estúdio de composição/arranjo com IA local + notação, pensado para o chip M4 e a sua biblioteca Apple Music.
