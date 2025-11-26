// Глобальные переменные
const API_BASE = '/api/v1/signature';

let registrationNumber = null;
let currentFileUrl = null;
let selectedCertificateIndex = null;
let certificates = [];
let cadespluginLoaded = false;


function getRegistrationNumberFromUrl() {
    const url = window.location.href;

    const parts = url.split('/');
    registrationNumber = parts[parts.length - 1];
}

// Инициализация плагина
function initializePlugin() {
    const statusDiv = document.getElementById('pluginStatus');

    if (typeof cadesplugin === 'undefined') {
        statusDiv.innerHTML = '<div class="status error">КриптоПРО плагин не найден. Установите КриптоПРО Browser Plugin.</div>';
        return;
    }

    statusDiv.innerHTML = '<div class="status info">Инициализация плагина...</div>';

    cadesplugin.then(function() {
        cadespluginLoaded = true;
        statusDiv.innerHTML = '<div class="status success">Плагин успешно инициализирован!</div>';
        document.getElementById('loadCertsBtn').disabled = false;
        getRegistrationNumberFromUrl();
    }).catch(function(err) {
        statusDiv.innerHTML = `<div class="status error">Ошибка инициализации плагина: ${err.message}</div>`;
    });
}

// Загрузка сертификатов через CAPICOM.Store
function loadCertificates() {
    if (!cadespluginLoaded) {
        alert('Сначала инициализируйте плагин');
        return;
    }

    const statusDiv = document.getElementById('certStatus');
    const listDiv = document.getElementById('certificatesList');

    statusDiv.innerHTML = '<div class="status info">Загрузка сертификатов...</div>';
    listDiv.innerHTML = '';

    cadesplugin.async_spawn(function*() {
        try {
            let oStore = yield cadesplugin.CreateObjectAsync("CAPICOM.Store");

            // Открываем хранилище сертификатов
            yield oStore.Open(
                cadesplugin.CAPICOM_CURRENT_USER_STORE,
                cadesplugin.CAPICOM_MY_STORE,
                cadesplugin.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED
            );

            // Получаем сертификаты
            let certs = yield oStore.Certificates;
            certs = yield certs.Find(cadesplugin.CAPICOM_CERTIFICATE_FIND_TIME_VALID);
            let certsCount = yield certs.Count;

            certificates = [];

            if (certsCount === 0) {
                statusDiv.innerHTML = '<div class="status warning">Сертификаты не найдены</div>';
                return;
            }

            statusDiv.innerHTML = `<div class="status info">Найдено сертификатов: ${certsCount}</div>`;

            // Загружаем информацию о каждом сертификате
            for (let i = 1; i <= certsCount; i++) {
                try {
                    let cert = yield certs.Item(i);
                    let subjectName = yield cert.SubjectName;
                    let issuerName = yield cert.IssuerName;
                    let validFrom = yield cert.ValidFromDate;
                    let validTo = yield cert.ValidToDate;
                    let hasPrivateKey = yield cert.HasPrivateKey();

                    let certInfo = {
                        certificate: cert,
                        subjectName: subjectName,
                        issuerName: issuerName,
                        validFrom: new Date(validFrom),
                        validTo: new Date(validTo),
                        hasPrivateKey: hasPrivateKey,
                        index: i - 1
                    };

                    certificates.push(certInfo);

                    // Создаем элемент для отображения сертификата
                    const certElement = document.createElement('div');
                    certElement.className = 'cert-item';
                    certElement.innerHTML = `
                        <strong>Сертификат ${i}</strong><br>
                        <strong>Владелец:</strong> ${subjectName}<br>
                        <strong>Издатель:</strong> ${issuerName}<br>
                        <strong>Действует с:</strong> ${new Date(validFrom).toLocaleDateString()}<br>
                        <strong>Действует по:</strong> ${new Date(validTo).toLocaleDateString()}<br>
                        <strong>Приватный ключ:</strong> ${hasPrivateKey ? '✅ Доступен' : '❌ Недоступен'}
                        <br><br>
                        ${hasPrivateKey ?
                            `<button onclick="selectCertificate(${i - 1})" style="background: #28a745;">Выбрать для подписания</button>` :
                            `<button disabled>Ключ недоступен</button>`
                        }
                    `;

                    listDiv.appendChild(certElement);

                } catch (certError) {
                    console.error(`Ошибка загрузки сертификата ${i}:`, certError);
                }
            }

            statusDiv.innerHTML = `<div class="status success">Успешно загружено ${certificates.length} сертификатов</div>`;
            oStore.Close();

        } catch (exc) {
            console.error('Ошибка загрузки сертификатов:', exc);
            statusDiv.innerHTML = `<div class="status error">Ошибка загрузки сертификатов: ${exc.message}</div>`;
        }
    });
}

// Выбор сертификата
async function selectCertificate(index) {
    selectedCertificateIndex = index;
    const certItems = document.querySelectorAll('.cert-item');
    certItems.forEach(item => item.classList.remove('selected'));
    certItems[index].classList.add('selected');

    const certInfo = certificates[index];
    document.getElementById('certStatus').innerHTML =
        `<div class="status success">Выбран сертификат: ${certInfo.subjectName}</div>`;
}

// Генерация PDF
async function generatePDF(owner, publisher, valid_from, valid_until) {
    const statusDiv = document.getElementById('generateStatus');
    try {
        statusDiv.innerHTML = '<div class="status info">Генерация документа...</div>';

        const response = await fetch(`${API_BASE}/generate-pdf/emblem/${registrationNumber}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                body: JSON.stringify({
                    owner: owner,
                    publisher: publisher,
                    valid_from: valid_from,
                    valid_until: valid_until
                })
            }
        });

        if (!response.ok) {
            throw new Error('Ошибка генерации документа');
        }

        const data = await response.json();
        currentFileUrl = data.file_url;
        statusDiv.innerHTML = `<div class="status success">
            Документ создан! ID: ${data.document_id}
        </div>`;

        // Активируем кнопку подписания если выбран сертификат
        if (selectedCertificateIndex !== null) {
            document.getElementById('signBtn').disabled = false;
        }

    } catch (error) {
        statusDiv.innerHTML = `<div class="status error">Ошибка: ${error.message}</div>`;
    }
}

// Подписание PDF (обновленная версия по примеру из статьи)
function signPDF() {
    if (selectedCertificateIndex === null || !currentDocumentId) {
        alert('Сначала выберите сертификат и сгенерируйте документ');
        return;
    }

    const statusDiv = document.getElementById('signStatus');
    statusDiv.innerHTML = '<div class="status info">Начало процесса подписания...</div>';

    const certInfo = certificates[selectedCertificateIndex];

    await generatePDF(certInfo.subjectName, certInfo.issuerName, certInfo.validFrom, certInfo.validTo);

    cadesplugin.async_spawn(function*() {
        try {
            let cert = certInfo.certificate;
            // Получаем информацию о сертификате для диагностики
            let certSubject = yield cert.SubjectName;
            let certThumbprint = yield cert.Thumbprint;

            var fileData = yield loadFileFromUrl(currentFileUrl);

            var oSigner = yield cadesplugin.CreateObjectAsync("CAdESCOM.CPSigner");
            yield oSigner.propset_Certificate(cert);
            yield oSigner.propset_CheckCertificate(true);

            var oSignature = yield cadesplugin.CreateObjectAsync("CAdESCOM.CPSignature");

            // Настраиваем параметры визуальной подписи
            yield oSignature.propset_Reason("Документ подписан электронной подписью");
            yield oSignature.propset_Location("Москва");
            yield oSignature.propset_ContactInfo("email@example.com");

            // Привязываем визуальное представление к подписанту
            yield oSigner.propset_Signature(oSignature);

            var oSignedData = yield cadesplugin.CreateObjectAsync("CAdESCOM.CadesSignedData");
            yield oSignedData.propset_ContentEncoding(cadesplugin.CADESCOM_BASE64_TO_BINARY);
            yield oSignedData.propset_Content(fileData);

            var sSignedMessage;
            try {
                sSignedMessage = yield oSignedData.SignCades(
                    oSigner,
                    cadesplugin.CADESCOM_CADES_BES,
                    false
                );
            } catch (err) {
                alert("Failed to create signature. Error: " + cadesplugin.getLastError(err));
                return;
            }

            var oSignedData2 = yield cadesplugin.CreateObjectAsync("CAdESCOM.CadesSignedData");
            try {
                yield oSignedData2.propset_ContentEncoding(cadesplugin.CADESCOM_BASE64_TO_BINARY);
                yield oSignedData2.propset_Content(fileData);
                yield oSignedData2.VerifyCades(
                    sSignedMessage,
                    cadesplugin.CADESCOM_CADES_BES,
                    false
                );
                alert("Signature verified successfully for file: " + fileName);
            } catch (err) {
                alert("Failed to verify signature. Error: " + cadesplugin.getLastError(err));
                return;
            }

            // Отправляем подпись на сервер для верификации и сохранения
            statusDiv.innerHTML += '<div class="status info">Отправка подписи на сервер...</div>';

            var fileName = getFileNameFromUrl(currentFileUrl);
            var signedFileName = "signed_" + fileName;

            // Создаем blob из base64 данных
            var binaryString = atob(pdfData);
            var bytes = new Uint8Array(binaryString.length);
            for (var i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            var blob = new Blob([bytes], { type: 'application/pdf' });

            // Создаем FormData для отправки файла
            var formData = new FormData();
            formData.append('file', blob, signedFileName);
            formData.append('originalFileName', fileName);
            formData.append('uploadTimestamp', new Date().toISOString());

            // Отправляем на сервер
            return fetch(`${API_BASE}/load-pdf/signed/${registrationNumber}`, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Ошибка загрузки файла');
                }
                return response.json();
            })
            .then(result => {
                const downloadBtn = document.getElementById("downloadBtn");
                downloadBtn.onclick = downloadSignedPDF(result.file_url);
                downloadBtn.disabled = false;
                statusDiv.innerHTML += '<div class="status info">Документ успешно подписан</div>';
                return result;
            })
            .catch(error => {
                throw new Error('Ошибка при загрузке PDF');
            });

            } catch (serverError) {
                throw new Error('Не удалось отправить подпись на сервер');
            }

        } catch (exc) {
            statusDiv.innerHTML += `<div class="status info">${exc}</div>`;
        }
    });
}

// Функция для загрузки файла по URL
function loadFileFromUrl(url) {
    return new Promise((resolve, reject) => {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', url, true);
        xhr.responseType = 'blob';

        xhr.onload = function() {
            if (xhr.status === 200) {
                var blob = xhr.response;
                var reader = new FileReader();

                reader.onload = function() {
                    var base64 = reader.result.split(',')[1];
                    resolve(base64);
                };

                reader.onerror = function() {
                    reject(new Error('Failed to read blob as base64'));
                };

                reader.readAsDataURL(blob);
            } else {
                reject(new Error('Failed to load file: ' + xhr.statusText));
            }
        };

        xhr.onerror = function() {
            reject(new Error('Network error while loading file'));
        };

        xhr.send();
    });
}

function downloadSignedPDF(url) {
    // Создаем ссылку для скачивания
    var a = document.createElement('a');
    a.href = url;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Функция для извлечения имени файла из URL
function getFileNameFromUrl(url) {
    return url.substring(url.lastIndexOf('/') + 1);
}

// Автоматическая инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    if (typeof cadesplugin !== 'undefined') {
        initializePlugin();
    } else {
        document.getElementById('pluginStatus').innerHTML =
            '<div class="status error">КриптоПРО плагин не загружен. Проверьте подключение скрипта.</div>';
    }
});