# Activity Tracker

<p align="center">
  <img src="docs/activity-tracker-logo.png" alt="Activity Tracker logo" width="320">
</p>

[![Quality Gate](https://sonar.alves-dev.com/api/project_badges/measure?project=ha-activity-tracker&metric=alert_status)](https://sonar.alves-dev.com/dashboard?id=ha-activity-tracker)
[![Coverage](https://sonar.alves-dev.com/api/project_badges/measure?project=ha-activity-tracker&metric=coverage)](https://sonar.alves-dev.com/dashboard?id=ha-activity-tracker)
![Version](https://img.shields.io/badge/Version-2026.8.1-41BDF5?style=flat-square)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.8%2B-41BDF5?logo=homeassistant)

Track how long an entity, person, zone, area-presence sensor, or foreground application is active in Home Assistant.

Activity Tracker observes state changes live and stores compact daily summaries, so reports continue to work beyond Recorder retention. Each configured monitor is a separate Home Assistant device with only the entities selected during setup.

## Features

- Entity/generic active-state, zone, area-presence, and foreground-application monitors.
- Daily, current-week, current-month, and custom rolling calendar-day durations.
- Session counts, duration statistics, current activity, and latest completed-session details.
- Session splitting at local midnight, configurable minimum session duration, per-monitor retention, and foreground-app aggregation.
- UI-only setup and options; no YAML configuration.

## HACS availability

Activity Tracker is available as a **HACS custom repository** (category: **Integration**). It is not currently in the default HACS catalog: `https://github.com/alves-dev/ha-activity-tracker`.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=alves-dev&repository=ha-activity-tracker&category=integration)

## Installation

In HACS, add this repository as a **Custom repository** with category **Integration**, then install it and restart Home Assistant. Alternatively, copy `custom_components/activity_tracker` into your Home Assistant configuration directory and restart.

## Configuration and operation

Add **Activity Tracker** from *Settings → Devices & services → Add integration*. The guided flow selects the monitor source, behavior, report periods, and exactly which metric entities to create for each period. At least one report metric and one period are required.

### [pt-BR] Tipos de monitor

| Tipo                              | Quando usar                                                      | O que conta como atividade                                                                  | Caso de uso                                                              |
|-----------------------------------|------------------------------------------------------------------|---------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| Estados ativos de entidade        | Uma entidade já expõe estados significativos.                    | O estado é um dos valores informados, separados por vírgula.                                | [Tempo de TV ligada](docs/use-case-entity-active-states.md)              |
| Pessoa ou dispositivo em uma zona | Um `person` ou `device_tracker` informa o nome da zona desejada. | O estado corresponde exatamente à zona selecionada.                                         | [Visitas à academia](docs/use-case-zone.md)                              |
| Pessoa em uma área interna        | Um sensor binário identifica se uma pessoa está em uma área.     | O sensor binário de presença escolhido está em `on`; pessoa e área dão contexto ao monitor. | [Tempo no escritório](docs/use-case-area-presence.md)                    |
| Aplicativo em primeiro plano      | Uma entidade informa o aplicativo que está sendo usado.          | Há um valor não vazio no estado ou atributo; trocar de aplicativo inicia outra sessão.      | [Uso de aplicativos no celular](docs/use-case-foreground-application.md) |
| Regra de estado personalizada     | Você precisa de um monitor neutro baseado em estados.            | O estado é um dos valores ativos informados.                                                | [Ciclos da lavadora](docs/use-case-custom-state-rule.md)                 |

### [en] Monitor types

| Type                       | When to use it                                                | What counts as activity                                                                     | Use case                                                     |
|----------------------------|---------------------------------------------------------------|---------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| Entity active states       | An entity already exposes meaningful states.                  | Its state matches one of the comma-separated values you provide.                            | [TV-on time](docs/use-case-entity-active-states.md)          |
| Person or device in a zone | A `person` or `device_tracker` reports the desired zone name. | Its state exactly matches the selected zone.                                                | [Gym visits](docs/use-case-zone.md)                          |
| Person in an internal area | A binary sensor detects whether one person is in an area.     | The selected presence binary sensor is `on`; the person and area provide monitor context.   | [Time in the office](docs/use-case-area-presence.md)         |
| Foreground application     | An entity reports the application currently in use.           | A non-empty state or attribute value is present; changing application starts a new session. | [Mobile app usage](docs/use-case-foreground-application.md)  |
| Custom state rule          | You need a neutral state-based monitor.                       | Its state matches one of the active values you provide.                                     | [Washing-machine cycles](docs/use-case-custom-state-rule.md) |

### [pt-BR] Sensores que podem ser escolhidos

Durante a configuração, escolha um ou mais períodos (hoje, semana atual, mês
atual ou uma faixa móvel de dias) e, em seguida, escolha os sensores de relatório
para cada período. Os sensores marcados como **por período** são criados somente
nos períodos em que forem selecionados; os demais são criados uma única vez por
monitor. Por exemplo, você pode criar **Duração média das sessões** apenas para
os últimos 30 dias, sem criá-la para hoje.

| Sensor selecionável              | O que mostra                                                                   | Criação             |
|----------------------------------|--------------------------------------------------------------------------------|---------------------|
| Duração total da atividade       | Tempo total em atividade.                                                      | Por período         |
| Número de sessões                | Quantidade de sessões iniciadas.                                               | Por período         |
| Duração média diária             | Média de tempo de atividade por dia.                                           | Por período         |
| Duração média das sessões        | Média de duração das sessões.                                                  | Por período         |
| Duração da sessão mais longa     | Maior duração de sessão observada.                                             | Por período         |
| Duração da sessão mais curta     | Menor duração de sessão observada.                                             | Por período         |
| Tempo com estado desconhecido    | Tempo em que não foi possível determinar se havia atividade.                   | Por período         |
| Duração da sessão atual          | Tempo acumulado na sessão em andamento.                                        | Uma vez por monitor |
| Duração da última sessão         | Duração da sessão concluída mais recente.                                      | Uma vez por monitor |
| Início da última sessão          | Data e hora de início da sessão concluída mais recente.                        | Uma vez por monitor |
| Fim da última sessão             | Data e hora de fim da sessão concluída mais recente.                           | Uma vez por monitor |
| Dias desde a última sessão       | Dias desde o fim da sessão concluída mais recente.                             | Uma vez por monitor |
| Primeiro horário de atividade    | Primeiro horário de atividade de hoje.                                         | Uma vez por monitor |
| Último horário de atividade      | Último horário de atividade de hoje.                                           | Uma vez por monitor |
| Dia da semana com mais atividade | Dia da semana com o maior total de atividade entre os dados completos retidos. | Uma vez por monitor |

Todo monitor também cria automaticamente o sensor binário **Active**, que indica
se está ativo agora. Monitores de aplicativo em primeiro plano criam também o
sensor **Current foreground application**; esses dois sensores não são opções da
lista acima.

### [en] Selectable sensors

During setup, choose one or more periods (today, current week, current month,
or a rolling range of days), then choose the report sensors for each period.
Sensors marked **per period** are created only for periods where you select them;
all others are created once per monitor. For example, you can create **Average
session duration** only for the last 30 days, without creating it for today.

| Selectable sensor          | What it reports                                                        | Created          |
|----------------------------|------------------------------------------------------------------------|------------------|
| Total activity duration    | Total time spent active.                                               | Per period       |
| Number of sessions         | Number of started sessions.                                            | Per period       |
| Average daily duration     | Average active time per day.                                           | Per period       |
| Average session duration   | Average session duration.                                              | Per period       |
| Longest session duration   | Longest observed session duration.                                     | Per period       |
| Shortest session duration  | Shortest observed session duration.                                    | Per period       |
| Unknown-state duration     | Time during which activity could not be determined.                    | Per period       |
| Current session duration   | Time accumulated in the session in progress.                           | Once per monitor |
| Last session duration      | Duration of the most recently completed session.                       | Once per monitor |
| Last session start         | Start date and time of the most recently completed session.            | Once per monitor |
| Last session end           | End date and time of the most recently completed session.              | Once per monitor |
| Days since last session    | Days since the end of the most recently completed session.             | Once per monitor |
| First activity time        | First activity time today.                                             | Once per monitor |
| Last activity time         | Last activity time today.                                              | Once per monitor |
| Weekday with most activity | Weekday with the greatest activity total among retained complete data. | Once per monitor |

Every monitor also automatically creates the **Active** binary sensor, which
indicates whether it is active now. Foreground-application monitors also create
the **Current foreground application** sensor; neither is an option in the list
above.

### Session behavior in plain language

- **Retention** is how many local calendar days of compact summaries remain available. It is not a copy of Recorder history.
- **Minimum session duration** filters out completed sessions shorter than the chosen number of seconds. Set it to `0` to retain every completed session.
- **Unavailable tolerance** applies when Home Assistant cannot read the source. It is different from a **merge gap**, which applies when the source explicitly reports an inactive state for a short interval (for example, noisy GPS).
- **Rolling days** are calendar dates: “35 days” includes today and the 34 preceding local dates, rather than exactly 840 hours.

While a monitor is active, its current-session entity updates every minute without rewriting storage. Completed valid sessions are consolidated into local-calendar daily summaries. A session that crosses midnight contributes duration to both days, but counts only on its start date.

Foreground-application monitors treat an application switch as the end of one session and beginning of another. Application identifiers remain stable even when labels change.

## Technical documentation

- [Compatibility](docs/compatibility.md)
- [Development and validation](docs/development.md)
- [Storage and entity behavior](docs/architecture.md)

## License

MIT. See [LICENSE](LICENSE).
