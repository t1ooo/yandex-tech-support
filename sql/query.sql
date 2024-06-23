-- a) Выведи ники клиентов, поставивших csat меньше 3;

-- если ники у клиентов уникальны
SELECT DISTINCT(username)
FROM clients
INNER JOIN tickets ON username = tickets.ticket_client
WHERE csat < 3;

-- если нет (скорее всего)
SELECT DISTINCT(username)
FROM clients
INNER JOIN orders ON client_id = orders.order_client_id
INNER JOIN tickets ON orders.order_id = tickets.ticket_order_id
WHERE csat < 3;


-- б) Напиши SQL запрос, который вернет id тикетов, в тексте которых содержится слово “отлично” и отсортируй их по убыванию ксата;

-- text и csat вывел для наглядности
SELECT ticket_id, text, csat
FROM tickets
WHERE text REGEXP "\\bотлично\\b"
ORDER BY csat DESC;


-- в) Напиши SQL запрос, который вернет id клиентов, сделавших больше пяти заказов в ресторанах “Теремок” и “Вкусно и точка” на сумму от двух до десяти тысяч рублей. Также запрос должен вернуть сумму их самого дорогого заказа для этого фильтра. Полученные столбцы назови “frequent_customer” и “max_sum”;

SELECT order_client_id as frequent_customer, MAX(price) as max_sum
FROM orders
WHERE place IN ("Теремок", "Вкусно и точка")
GROUP BY order_client_id
HAVING SUM(price) BETWEEN 2000 AND 10000
    AND COUNT(*) >= 5
;


-- г) Дополнительное задание
-- Напиши SQL запрос, который дополнит таблицу orders данными из таблиц clients и tickets и вернет только 1000 записей из полученной таблицы.

SELECT orders.*, 
    clients.username, clients.name, clients.age, clients.city,
    tickets.ticket_id, tickets.csat, tickets.text, tickets.date
FROM orders
LEFT JOIN tickets ON order_id = tickets.ticket_order_id
LEFT JOIN clients ON order_client_id = clients.client_id
LIMIT 1000;
