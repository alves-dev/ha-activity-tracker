# [pt-BR] Caso de uso: tempo de tela do celular

Use um monitor de **Celular em uso** para acompanhar por quanto tempo a tela de
um celular Android ficou interativa, sem deixar uma sessão aberta quando a
bateria acaba ou o aparelho perde a comunicação.

1. No aplicativo Home Assistant Companion do celular, habilite as entidades
   **Interactive** e **Last update trigger**.
2. Crie um monitor e escolha **Celular em uso**.
3. Selecione o dispositivo do celular; não escolha entidades individualmente.
4. Defina o limite sem comunicação. O padrão é 1800 segundos (30 minutos),
   adequado à atualização periódica normal do Android.
5. Escolha os períodos e sensores de duração ou sessão desejados.

Enquanto **Interactive** estiver em `on`, a atividade continua apenas enquanto
o Companion App confirma que o telefone está se comunicando. Ao expirar o
limite, o monitor aplica o comportamento de fonte indisponível — novos monitores
encerram a sessão por padrão. Uma atualização de heartbeat não reabre uma
sessão; uma nova observação da tela interativa é necessária.

Este tipo começa a medir a partir da configuração e não oferece importação do
Recorder, pois o histórico não consegue reconstruir com segurança relatórios de
heartbeat sem mudança de estado.

---

# [en] Use case: phone screen time

Use a **Mobile device in use** monitor to track how long an Android phone's
screen was interactive without leaving a session open when the battery dies or
the device loses communication.

1. In the phone's Home Assistant Companion App, enable **Interactive** and
   **Last update trigger**.
2. Create a monitor and choose **Mobile device in use**.
3. Select the phone device; do not select individual entities.
4. Set the no-communication limit. The default is 1800 seconds (30 minutes),
   matching Android's normal periodic update cadence.
5. Select the desired periods and duration or session sensors.

While **Interactive** is `on`, activity continues only while the Companion App
confirms that the phone is communicating. At the deadline, the monitor applies
the unavailable-source behavior — new monitors end the session by default. A
heartbeat report never reopens a session; a new interactive-screen observation
is required.

This monitor starts collecting from setup and does not offer Recorder import,
because history cannot safely reconstruct unchanged heartbeat reports.
