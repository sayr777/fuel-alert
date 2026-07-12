import type { CSSProperties } from "react";
import { TELEGRAM_BOT_URL } from "../config";
import type { EventType } from "../types";
import "./Landing.css";

interface Props {
  eventTypes: EventType[];
  onOpenMap: () => void;
}

export default function Landing({ eventTypes, onOpenMap }: Props) {
  const available = eventTypes.filter((et) => !et.requires_moderation);
  const violations = eventTypes.filter((et) => et.requires_moderation);
  const fuelType = eventTypes.find((et) => et.attributes.includes("fuel_grades"));

  return (
    <div className="landing">
      <div className="hazard" />

      <header className="wrap nav">
        <div className="disp fw8 fs16">
          ТОПЛИВНЫЙ ДОЗОР<span className="acc">.</span>
        </div>
        <div className="f1" />
        <a className="navl" href="#events">
          События
        </a>
        <a className="navl" href="#bot">
          Бот
        </a>
        <a className="navl" href="#about">
          О проекте
        </a>
        <button className="navl navbtn" onClick={onOpenMap}>
          Карта
        </button>
      </header>

      <section className="hero">
        <div className="gridbg" />
        <div className="wrap posrel">
          <div className="kick">Народный мониторинг АЗС</div>
          <h1 className="htitle m0">
            Куда пропал
            <br />
            бензин —
            <br />
            <span className="acc">знают водители</span>
          </h1>
          <p className="lead">
            «Топливный Дозор» — карта топливной ситуации по всей России, которую заполняют сами
            водители через Telegram-бота: где нет 92-го, где лимит на 95-й, а где торгуют из канистр.
            Каждое обращение проходит автоматическую проверку и попадает на общую карту.
          </p>
          <div className="hero-actions">
            <a className="btn btn-p" href={TELEGRAM_BOT_URL} target="_blank" rel="noopener noreferrer">
              Сообщить в боте
            </a>
            <button className="btn btn-g" onClick={onOpenMap}>
              Открыть карту
            </button>
          </div>
          <div className="feat">
            <div className="fchip">
              <span className="dot" style={{ background: eventTypes[0]?.color ?? "var(--accent)" }} />
              {eventTypes.length || "—"} типов событий
            </div>
            <div className="fchip">Фото — не более 2</div>
            <div className="fchip">Геопозиция и время обязательны</div>
            <div className="fchip">Публично только ники, без телефонов</div>
          </div>
        </div>
      </section>

      <section className="sec wrap" id="events">
        <div className="kick">01 · Классификатор</div>
        <h2 className="h2 m0">Типы событий</h2>
        <p className="lead">
          Каждому типу — свой цвет маркера на карте. События без пометки публикуются сразу,
          «Нарушения и мошенничество» проходят ручную модерацию.
        </p>

        <div className="grouplbl">Доступность и обслуживание</div>
        <div className="ecards">
          {available.map((et) => (
            <div key={et.code} className="card ecard" style={{ "--c": et.color } as CSSProperties}>
              <div className="fx ac gap10">
                <span className="dot" />
                <span className="ecode mono">{et.code}</span>
              </div>
              <div className="ename">{et.label_ru}</div>
              <div className="enote">
                {et.attributes.includes("fuel_grades")
                  ? "Требует выбора марки топлива. "
                  : ""}
                Актуально {et.ttl_hours} ч.
              </div>
            </div>
          ))}
        </div>

        <div className="grouplbl">Нарушения и мошенничество</div>
        <div className="ecards">
          {violations.map((et) => (
            <div key={et.code} className="card ecard" style={{ "--c": et.color } as CSSProperties}>
              <div className="fx ac gap10">
                <span className="dot" />
                <span className="ecode mono">{et.code}</span>
              </div>
              <div className="ename">{et.label_ru}</div>
              <div className="enote">Публикуется только после проверки модератором.</div>
            </div>
          ))}
        </div>
      </section>

      <section className="sec wrap">
        <div className="kick">02 · Как это работает</div>
        <h2 className="h2 m0">От сообщения до маркера на карте</h2>
        <div className="steps">
          <div className="card step">
            <div className="stepn disp">01</div>
            <div className="stept">Водитель сообщает в боте</div>
            <div className="stepd">
              Тип события, при необходимости марки топлива и другие детали, геопозиция, до 2 фото и
              короткое описание. Меньше минуты.
            </div>
          </div>
          <div className="card step">
            <div className="stepn disp">02</div>
            <div className="stept">Проверка и склейка</div>
            <div className="stepd">
              Автовалидация: гео в зоне покрытия, событие не старше срока давности, дедупликация
              повторов рядом по месту и времени. Чувствительные категории — через модератора.
            </div>
          </div>
          <div className="card step">
            <div className="stepn disp">03</div>
            <div className="stept">Событие на карте</div>
            <div className="stepd">
              Маркер с цветом типа появляется на публичной карте. Виден ник автора, фото и число
              подтверждений. Телефоны не публикуются никогда.
            </div>
          </div>
        </div>
      </section>

      <section className="sec wrap" id="bot">
        <div className="kick">03 · Telegram-бот</div>
        <h2 className="h2 m0">Сценарий отправки обращения</h2>
        <p className="lead">
          Пошаговый диалог с инлайн-кнопками: без геопозиции и типа события обращение не отправить,
          лишнее фото бот отклонит.
        </p>
        <div className="phones">
          <div className="phcol">
            <div className="ph">
              <div className="tg">
                <div className="tgh">
                  <div className="tgav">Д</div>
                  <div>
                    <div className="tgn">Топливный Дозор</div>
                    <div className="tgo">бот · онлайн</div>
                  </div>
                </div>
                <div className="tgb">
                  <div className="bo">/report</div>
                  <div className="bi">Что случилось? Выберите тип события:</div>
                  <div className="ikb">
                    {eventTypes.slice(0, 6).map((et) => (
                      <div key={et.code} className="ikbtn" style={{ "--c": et.color } as CSSProperties}>
                        <span className="dots" />
                        {et.label_ru}
                      </div>
                    ))}
                  </div>
                  {fuelType && <div className="bo">{fuelType.label_ru}</div>}
                </div>
              </div>
            </div>
            <div className="phcap">
              <span className="phcapn">ШАГ 1</span>
              <br />
              Тип события — инлайн-кнопки по классификатору
            </div>
          </div>

          <div className="phcol">
            <div className="ph">
              <div className="tg">
                <div className="tgh">
                  <div className="tgav">Д</div>
                  <div>
                    <div className="tgn">Топливный Дозор</div>
                    <div className="tgo">бот · онлайн</div>
                  </div>
                </div>
                <div className="tgb">
                  <div className="bi">Какие марки топлива? Можно выбрать несколько:</div>
                  <div className="ikb" style={{ gridTemplateColumns: "repeat(3,1fr)" }}>
                    <div className="ikbtn">АИ-92 ✓</div>
                    <div className="ikbtn">АИ-95 ✓</div>
                    <div className="ikbtn">АИ-98</div>
                    <div className="ikbtn">АИ-100</div>
                    <div className="ikbtn">ДТ</div>
                    <div className="ikbtn">Газ</div>
                    <div className="ikbtn ikw">✔️ Готово</div>
                  </div>
                  <div className="bi">📍 Отправьте геолокацию события.</div>
                  <div className="ikb">
                    <div className="ikbtn ikw">Отправить геолокацию</div>
                  </div>
                </div>
              </div>
            </div>
            <div className="phcap">
              <span className="phcapn">ШАГ 2</span>
              <br />
              Марки топлива и обязательная геопозиция
            </div>
          </div>

          <div className="phcol">
            <div className="ph">
              <div className="tg">
                <div className="tgh">
                  <div className="tgav">Д</div>
                  <div>
                    <div className="tgn">Топливный Дозор</div>
                    <div className="tgo">бот · онлайн</div>
                  </div>
                </div>
                <div className="tgb">
                  <div className="bi">
                    Прикрепите фотографии — максимум две — файлом, чтобы сохранить EXIF. Можно
                    пропустить.
                  </div>
                  <div className="ikb">
                    <div className="ikbtn ikw">Пропустить фото →</div>
                  </div>
                  <div className="bo">
                    <div className="photos">
                      <div className="pho">IMG_0231</div>
                      <div className="pho">IMG_0232</div>
                    </div>
                  </div>
                  <div className="bi">Добавьте короткое описание ситуации.</div>
                </div>
              </div>
            </div>
            <div className="phcap">
              <span className="phcapn">ШАГ 3</span>
              <br />
              До 2 фото файлом + текстовое описание
            </div>
          </div>

          <div className="phcol">
            <div className="ph">
              <div className="tg">
                <div className="tgh">
                  <div className="tgav">Д</div>
                  <div>
                    <div className="tgn">Топливный Дозор</div>
                    <div className="tgo">бот · онлайн</div>
                  </div>
                </div>
                <div className="tgb">
                  <div className="bi">
                    <div className="prev" style={{ "--c": fuelType?.color ?? "#FF4B3E" } as CSSProperties}>
                      <span className="ebadge">
                        <span className="dot" />
                        {fuelType?.label_ru ?? "Топливо отсутствует"}
                      </span>
                      <div>
                        <div className="prevlbl">Марки</div>
                        <div className="prevrow">АИ-92, АИ-95</div>
                      </div>
                      <div>
                        <div className="prevlbl">Место</div>
                        <div className="prevrow">53.0440, 158.6310</div>
                      </div>
                      <div className="prevrow">«На всех колонках табличка «топливо закончилось»…»</div>
                    </div>
                  </div>
                  <div className="ikb">
                    <div className="ikbtn">Изменить</div>
                    <div className="ikbtn">❌ Отмена</div>
                    <div className="ikbtn ikw">✅ Отправить</div>
                  </div>
                </div>
              </div>
            </div>
            <div className="phcap">
              <span className="phcapn">ШАГ 4</span>
              <br />
              Предпросмотр обращения перед отправкой
            </div>
          </div>

          <div className="phcol">
            <div className="ph">
              <div className="tg">
                <div className="tgh">
                  <div className="tgav">Д</div>
                  <div>
                    <div className="tgn">Топливный Дозор</div>
                    <div className="tgo">бот · онлайн</div>
                  </div>
                </div>
                <div className="tgb">
                  <div className="bo">✅ Отправить</div>
                  <div className="bi">
                    Принято. Обращение <span className="mono">#4821</span> отправлено на проверку.
                    <div className="mt8">
                      <span className="statchip">На модерации</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="phcap">
              <span className="phcapn">ШАГ 5</span>
              <br />
              Статус обращения — публикация или модерация
            </div>
          </div>
        </div>
      </section>

      <section className="sec wrap">
        <div className="kick">04 · Публичный фронт</div>
        <h2 className="h2 m0">Карта событий</h2>
        <p className="lead">
          Фильтры по типам, маркам топлива и периоду. Список синхронизирован с видимой областью
          карты.
        </p>
        <button className="card showcase-cta" onClick={onOpenMap}>
          <span>Открыть карту событий</span>
          <span className="acc">→</span>
        </button>
      </section>

      <section className="sec wrap" id="about">
        <div className="kick">05 · О проекте</div>
        <h2 className="h2 m0">Карта, которую рисуют сами водители</h2>
        <p className="lead">
          Официальные данные о заправках всегда отстают от реальности. Единственный надёжный
          источник — водители, которые прямо сейчас стоят у колонки и знают, есть ли топливо.
          «Топливный Дозор» построен на этом принципе.
        </p>

        <div className="steps">
          <div className="card step">
            <div className="stepn disp">2007</div>
            <div className="stept">Ushahidi, Кения</div>
            <div className="stepd">
              Жители сообщали об очагах насилия через SMS — точки на карте помогали
              гуманитарным службам ориентироваться в кризисе. Технология проста: свидетель
              видит, сообщает — все видят.
            </div>
          </div>
          <div className="card step">
            <div className="stepn disp">2011</div>
            <div className="stept">РосЯма, Россия</div>
            <div className="stepd">
              Водители фотографировали дорожные ямы, система автоматически отправляла
              официальные жалобы. Каждый дефект становился публичной точкой на карте, которую
              нельзя было игнорировать.
            </div>
          </div>
          <div className="card step">
            <div className="stepn disp">сегодня</div>
            <div className="stept">Яндекс Пробки</div>
            <div className="stepd">
              Миллионы смартфонов передают анонимные данные о скорости — алгоритм собирает их
              в живую карту трафика. Каждый водитель одновременно потребитель и источник
              данных.
            </div>
          </div>
        </div>

        <p className="about-body">
          «Топливный Дозор» применяет тот же принцип к топливу. Водитель за несколько секунд
          сообщает через Telegram-бота: нет бензина, есть лимит, завышена цена на табло. Информация
          сразу появляется на карте для всех остальных. Один человек сэкономил время десяткам
          других. Завтра кто-то другой предупредит его. Чем больше участников — тем точнее и
          актуальнее картина.
        </p>
      </section>

      <footer className="foot wrap">
        <div className="kick">Приватность</div>
        <div className="card privacy">
          <span className="dot" style={{ "--c": "#3DDC84" } as CSSProperties} />
          <div className="fs14 privacy-text">
            Наружу отдаются только ники. Телефон и Telegram-ID хранятся закрыто и используются
            исключительно для верификации и антиспама. Фото — в объектном хранилище, в базе только
            ссылки.
          </div>
        </div>
        <div className="mono fs12 mut copyright">ТОПЛИВНЫЙ ДОЗОР</div>
      </footer>

      <div className="hazard" style={{ marginTop: 56 }} />
    </div>
  );
}
