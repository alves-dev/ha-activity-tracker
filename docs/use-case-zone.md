# [pt-BR] Caso de uso: visitas à academia

Use um monitor de **Pessoa ou dispositivo em uma zona** para medir o tempo que
alguém passa em uma zona do Home Assistant, como a academia.

1. Crie a zona da academia no Home Assistant, se ela ainda não existir.
2. Crie um monitor e escolha **Pessoa ou dispositivo em uma zona**.
3. Selecione a pessoa ou o `device_tracker` e escolha a zona da academia.
4. Escolha sensores como **Duração total da atividade**, **Número de sessões**
   e **Duração média das sessões**.

Uma sessão começa quando a fonte passa a informar a zona selecionada e termina
quando ela informa outro local. Para a zona de casa, o valor reconhecido é
`home`.

---

# [en] Use case: gym visits

Use a **Person or device in a zone** monitor to measure how long someone spends
in a Home Assistant zone, such as a gym.

1. Create the gym zone in Home Assistant if it does not already exist.
2. Create a monitor and choose **Person or device in a zone**.
3. Select the person or `device_tracker`, then choose the gym zone.
4. Select sensors such as **Total activity duration**, **Number of sessions**,
   and **Average session duration**.

A session starts when the source reports the selected zone and ends when it
reports another location. For the home zone, the recognized value is `home`.
