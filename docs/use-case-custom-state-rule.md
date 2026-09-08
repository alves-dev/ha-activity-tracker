# [pt-BR] Caso de uso: ciclos da lavadora

Use uma **Regra de estado personalizada** quando a entidade tem estados próprios
e você quer decidir explicitamente quais representam a atividade, como os ciclos
de uma lavadora.

1. Crie um monitor e escolha **Regra de estado personalizada**.
2. Selecione a entidade da lavadora.
3. Informe os estados ativos, por exemplo, `washing`, `rinsing` e `spinning`.
4. Selecione **Número de sessões**, **Duração total da atividade** e
   **Duração da sessão mais longa** para acompanhar os ciclos.

Estados fora da lista, como `idle` ou `finished`, não contam como atividade. A
lista pode usar os valores exatos expostos pela entidade, sem depender de uma
classe específica de dispositivo.

---

# [en] Use case: washing-machine cycles

Use a **Custom state rule** when an entity exposes its own states and you want
to explicitly decide which ones represent activity, such as washing-machine
cycles.

1. Create a monitor and choose **Custom state rule**.
2. Select the washing-machine entity.
3. Enter the active states, for example, `washing`, `rinsing`, and `spinning`.
4. Select **Number of sessions**, **Total activity duration**, and **Longest
   session duration** to follow the cycles.

States outside the list, such as `idle` or `finished`, do not count as
activity. The list can use the exact values exposed by the entity without
depending on a specific device class.
