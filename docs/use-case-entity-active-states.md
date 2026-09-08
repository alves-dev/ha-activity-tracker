# [pt-BR] Caso de uso: tempo de TV ligada

Use um monitor de **Estados ativos de entidade** para saber quanto tempo a TV
fica ligada por dia ou semana.

1. Crie um monitor e escolha **Estados ativos de entidade**.
2. Selecione, por exemplo, `media_player.sala`.
3. Informe os estados que representam uso, como `on`, `playing` e `paused`.
4. Selecione os períodos e sensores desejados, como **Duração total da
   atividade** e **Número de sessões**.

O monitor considera ativa apenas uma entidade cujo estado corresponda a um dos
estados informados. Passar de `playing` para `paused`, por exemplo, mantém a
mesma sessão porque ambos foram definidos como ativos.

---

# [en] Use case: TV-on time

Use an **Entity active states** monitor to learn how long the TV is on each day
or week.

1. Create a monitor and choose **Entity active states**.
2. Select, for example, `media_player.sala`.
3. Enter the states that represent use, such as `on`, `playing`, and `paused`.
4. Select the desired periods, then choose sensors for each one, such as
   **Total activity duration** and **Number of sessions**.

The monitor considers an entity active only while its state matches one of the
entered states. Moving from `playing` to `paused`, for example, keeps the same
session open because both are defined as active.
