# [pt-BR] Caso de uso: tempo no escritório

Use um monitor de **Pessoa em uma área interna** para acompanhar quanto tempo
uma pessoa permanece no escritório em casa.

1. Garanta que exista uma área chamada, por exemplo, Escritório e um sensor
   binário de presença confiável para a pessoa nessa área.
2. Crie um monitor e escolha **Pessoa em uma área interna**.
3. Selecione a pessoa, a área e o sensor binário de presença.
4. Escolha **Duração total da atividade** e **Primeiro horário de atividade**
   para visualizar o tempo e o início do expediente.

O que determina a atividade é o sensor binário em `on`. A pessoa e a área
servem para identificar claramente o monitor no Home Assistant.

---

# [en] Use case: time in the office

Use a **Person in an internal area** monitor to track how long a person remains
in a home office.

1. Ensure that an area such as Office exists and that a reliable binary
   presence sensor is available for the person in that area.
2. Create a monitor and choose **Person in an internal area**.
3. Select the person, the area, and the binary presence sensor.
4. Select **Total activity duration** and **First activity time** to see the
   working time and its start.

The binary sensor being `on` determines activity. The person and area identify
the monitor clearly in Home Assistant.
