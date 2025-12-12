--
-- PostgreSQL database dump
--


-- Dumped from database version 15.14 (Debian 15.14-1.pgdg13+1)
-- Dumped by pg_dump version 17.6 (Debian 17.6-0+deb13u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: delete_failed_expenses(integer, boolean, integer[]); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.delete_failed_expenses(_workspace_id integer, _delete_all boolean DEFAULT false, _expense_group_ids integer[] DEFAULT '{}'::integer[]) RETURNS void
    LANGUAGE plpgsql
    AS $$

DECLARE
  	rcount integer;
	temp_expenses integer[];
	local_expense_group_ids integer[];
	total_expense_groups integer;
	failed_expense_groups integer;
	_fyle_org_id text;
	expense_ids text;
BEGIN
  RAISE NOTICE 'Deleting failed expenses from workspace % ', _workspace_id;

local_expense_group_ids := _expense_group_ids;

IF _delete_all THEN
	-- Update last_export_details when delete_all is true
	select array_agg(expense_group_id) into local_expense_group_ids from task_logs where status='FAILED' and workspace_id=_workspace_id;
	UPDATE last_export_details SET failed_expense_groups_count = 0 WHERE workspace_id = _workspace_id;
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Updated % last_export_details', rcount;
END IF;

SELECT array_agg(expense_id) into temp_expenses from expense_groups_expenses where expensegroup_id in (SELECT unnest(local_expense_group_ids));

_fyle_org_id := (select fyle_org_id from workspaces where id = _workspace_id);
expense_ids := (
    select string_agg(format('%L', expense_id), ', ')
    from expenses
    where workspace_id = _workspace_id
    and id in (SELECT unnest(temp_expenses))
);

DELETE
	FROM task_logs WHERE workspace_id = _workspace_id AND status = 'FAILED' and expense_group_id in (SELECT unnest(local_expense_group_ids));
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % task_logs', rcount;

DELETE
	FROM errors
	where expense_group_id IN (SELECT unnest(local_expense_group_ids));
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % errors', rcount;

DELETE
	FROM expense_groups_expenses WHERE expensegroup_id IN (SELECT unnest(local_expense_group_ids));
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % expense_groups_expenses', rcount;

DELETE
	FROM expense_groups WHERE id in (SELECT unnest(local_expense_group_ids));
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % expense_groups', rcount;

IF NOT _delete_all THEN
    UPDATE last_export_details
        SET total_expense_groups_count = total_expense_groups_count - rcount,
            failed_expense_groups_count = failed_expense_groups_count - rcount,
            updated_at = NOW()
        WHERE workspace_id = _workspace_id;

    total_expense_groups := (SELECT total_expense_groups_count FROM last_export_details WHERE workspace_id = _workspace_id);
    failed_expense_groups := (SELECT failed_expense_groups_count FROM last_export_details WHERE workspace_id = _workspace_id);

    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Updated last_export_details';
    RAISE NOTICE 'New total_expense_groups_count: %', total_expense_groups;
    RAISE NOTICE 'New failed_expense_groups_count: %', failed_expense_groups;
END IF;


DELETE
	FROM expenses WHERE id in (SELECT unnest(temp_expenses));
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % expenses', rcount;


RAISE NOTICE E'\n\n\nProd DB Queries to delete accounting export summaries:';
RAISE NOTICE E'rollback; begin; update platform_schema.expenses_wot set accounting_export_summary = \'{}\' where org_id = \'%\' and id in (%); update platform_schema.reports_wot set accounting_export_summary = \'{}\' where org_id = \'%\' and id in (select report->>\'id\' from platform_schema.expenses_rov where org_id = \'%\' and id in (%));', _fyle_org_id, expense_ids, _fyle_org_id, _fyle_org_id, expense_ids;

RETURN;
END
$$;


ALTER FUNCTION public.delete_failed_expenses(_workspace_id integer, _delete_all boolean, _expense_group_ids integer[]) OWNER TO postgres;

--
-- Name: delete_test_orgs_schedule(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.delete_test_orgs_schedule() RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    rcount integer;
BEGIN

    DELETE FROM workspace_schedules
    WHERE workspace_id NOT IN (
        SELECT id FROM prod_workspaces_view
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % workspace_schedules', rcount;

    DELETE FROM django_q_schedule
    WHERE args NOT IN (
        SELECT id::text FROM prod_workspaces_view
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % django_q_schedule', rcount;
END;
$$;


ALTER FUNCTION public.delete_test_orgs_schedule() OWNER TO postgres;

--
-- Name: delete_workspace(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.delete_workspace(_workspace_id integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    rcount integer;
    _org_id varchar(255);
    _fyle_org_id text;
    expense_ids text;
BEGIN
    RAISE NOTICE 'Deleting data from workspace %', _workspace_id;

    _fyle_org_id := (select fyle_org_id from workspaces where id = _workspace_id);

    expense_ids := (
        select string_agg(format('%L', e.expense_id), ', ')
        from expenses e
        where e.workspace_id = _workspace_id
    );

    DELETE
    FROM dependent_field_settings dfs
    WHERE dfs.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % dependent_field_settings', rcount;

    DELETE
    FROM dimension_details dd
    WHERE dd.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % dimension_details', rcount;

    DELETE
    FROM intacct_sync_timestamps ist
    WHERE ist.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % intacct_sync_timestamps', rcount;

    DELETE
    FROM cost_codes cc
    WHERE cc.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % cost_codes', rcount;

    DELETE
    FROM cost_types ct
    WHERE ct.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % cost_types', rcount;

    DELETE
    FROM location_entity_mappings lem
    WHERE lem.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % location_entity_mappings', rcount;

    DELETE
    FROM expense_fields ef
    WHERE ef.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % expense_fields', rcount;

    DELETE
    FROM errors e
    WHERE e.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % errors', rcount;

    DELETE
    FROM import_logs il
    WHERE il.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % import_logs', rcount;

    DELETE
    FROM task_logs tl
    WHERE tl.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % task_logs', rcount;

    DELETE
    FROM bill_lineitems bl
    WHERE bl.bill_id IN (
        SELECT b.id FROM bills b WHERE b.expense_group_id IN (
            SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
        )
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % bill_lineitems', rcount;

    DELETE
    FROM bills b
    WHERE b.expense_group_id IN (
        SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % bills', rcount;

    DELETE
    FROM charge_card_transaction_lineitems cctl
    WHERE cctl.charge_card_transaction_id IN (
        SELECT cct.id FROM charge_card_transactions cct WHERE cct.expense_group_id IN (
            SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
        )
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % charge_card_transaction_lineitems', rcount;

    DELETE
    FROM charge_card_transactions cct
    WHERE cct.expense_group_id IN (
        SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % charge_card_transactions', rcount;

    DELETE
    FROM journal_entry_lineitems jel
    WHERE jel.journal_entry_id IN (
        SELECT je.id FROM journal_entries je WHERE je.expense_group_id IN (
            SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
        )
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % journal_entry_lineitems', rcount;

    DELETE
    FROM journal_entries je
    WHERE je.expense_group_id IN (
        SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % journal_entries', rcount;

    DELETE
    FROM expense_report_lineitems erl
    WHERE erl.expense_report_id IN (
        SELECT er.id FROM expense_reports er WHERE er.expense_group_id IN (
            SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
        )
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % expense_report_lineitems', rcount;

    DELETE
    FROM expense_reports er
    WHERE er.expense_group_id IN (
        SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % expense_reports', rcount;

    DELETE
    FROM ap_payment_lineitems apl
    WHERE apl.ap_payment_id IN (
        SELECT ap.id FROM ap_payments ap WHERE ap.expense_group_id IN (
            SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
        )
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % ap_payment_lineitems', rcount;

    DELETE
    FROM ap_payments ap
    WHERE ap.expense_group_id IN (
        SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % ap_payments', rcount;

    DELETE
    FROM sage_intacct_reimbursement_lineitems sirl
    WHERE sirl.sage_intacct_reimbursement_id IN (
        SELECT sir.id FROM sage_intacct_reimbursements sir WHERE sir.expense_group_id IN (
            SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
        )
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % sage_intacct_reimbursement_lineitems', rcount;

    DELETE
    FROM sage_intacct_reimbursements sir
    WHERE sir.expense_group_id IN (
        SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % sage_intacct_reimbursements', rcount;

    DELETE
    FROM reimbursements r
    WHERE r.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % reimbursements', rcount;

    DELETE
    FROM expenses e
    WHERE e.id IN (
        SELECT expense_id FROM expense_groups_expenses ege WHERE ege.expensegroup_id IN (
            SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
        )
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % expenses', rcount;

    DELETE
    FROM expenses
    WHERE is_skipped=true and org_id in (SELECT fyle_org_id FROM workspaces WHERE id=_workspace_id);
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % skipped expenses', rcount;

    DELETE
    FROM expense_groups_expenses ege
    WHERE ege.expensegroup_id IN (
        SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % expense_groups_expenses', rcount;

    DELETE
    FROM expense_groups eg
    WHERE eg.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % expense_groups', rcount;

    DELETE
    FROM mappings m
    WHERE m.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % mappings', rcount;

    DELETE
    FROM employee_mappings em
    WHERE em.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % employee_mappings', rcount;

    DELETE
    FROM category_mappings cm
    WHERE cm.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % category_mappings', rcount;

    DELETE
    FROM mapping_settings ms
    WHERE ms.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % mapping_settings', rcount;

    DELETE
    FROM general_mappings gm
    WHERE gm.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % general_mappings', rcount;

    DELETE
    FROM configurations c
    WHERE c.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % configurations', rcount;

    DELETE
    FROM expense_group_settings egs
    WHERE egs.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % expense_group_settings', rcount;

    DELETE
    FROM fyle_credentials fc
    WHERE fc.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % fyle_credentials', rcount;

    DELETE
    FROM sage_intacct_credentials sic
    WHERE sic.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % sage_intacct_credentials', rcount;

    DELETE
    FROM expense_attributes_deletion_cache ead
    WHERE ead.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % expense_attributes_deletion_cache', rcount;

    DELETE
    FROM expense_attributes ea
    WHERE ea.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % expense_attributes', rcount;

    DELETE
    FROM expense_filters ef
    WHERE ef.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % expense_filters', rcount;

    DELETE
    FROM destination_attributes da
    WHERE da.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % destination_attributes', rcount;

    DELETE
    FROM workspace_schedules wsch
    WHERE wsch.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % workspace_schedules', rcount;

    DELETE
    FROM last_export_details led
    WHERE led.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % last_export_details', rcount;

    DELETE
    FROM feature_configs fc
    WHERE fc.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % feature_configs', rcount;

    DELETE
    FROM fyle_sync_timestamps fst
    WHERE fst.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % fyle_sync_timestamps', rcount;

    DELETE
    FROM django_q_schedule dqs
    WHERE dqs.args = _workspace_id::varchar(255);
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % django_q_schedule', rcount;

    DELETE
    FROM auth_tokens aut
    WHERE aut.user_id IN (
        SELECT u.id FROM users u WHERE u.id IN (
            SELECT wu.user_id FROM workspaces_user wu WHERE workspace_id = _workspace_id
        )
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % auth_tokens', rcount;

    DELETE
    FROM workspaces_user wu
    WHERE workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % workspaces_user', rcount;

    DELETE
    FROM users u
    WHERE u.id IN (
        SELECT wu.user_id FROM workspaces_user wu WHERE workspace_id = _workspace_id
    );
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % users', rcount;

    _org_id := (SELECT fyle_org_id FROM workspaces WHERE id = _workspace_id);

    DELETE
    FROM workspaces w
    WHERE w.id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % workspaces', rcount;

    RAISE NOTICE E'\n\n\n\n\n\n\n\n\nSwitch to integration_settings db and run the below query to delete the integration';
    RAISE NOTICE E'\\c integration_settings; \n\n begin; select delete_integration(''%'');\n\n\n\n\n\n\n\n\n\n\n', _org_id;

    RAISE NOTICE E'\n\n\n\n\n\n\n\n\nSwitch to prod db and run the below query to update the subscription';
    RAISE NOTICE E'begin; update platform_schema.admin_subscriptions set is_enabled = false where org_id = ''%'';\n\n\n\n\n\n\n\n\n\n\n', _org_id;

    RAISE NOTICE E'\n\n\n\n\n\n\n\n\nSwitch to prod db and run the below queries to delete dependent fields';
    RAISE NOTICE E'rollback;begin; delete from platform_schema.dependent_expense_field_mappings where expense_field_id in (select id from platform_schema.expense_fields where org_id =''%'' and type=''DEPENDENT_SELECT''); delete from platform_schema.expense_fields where org_id = ''%'' and type = ''DEPENDENT_SELECT'';\n\n\n\n\n\n\n\n\n\n\n', _org_id, _org_id;

    RAISE NOTICE E'\n\n\nProd DB Queries to delete accounting export summaries:';
    RAISE NOTICE E'rollback; begin; update platform_schema.expenses_wot set accounting_export_summary = \'{}\' where org_id = \'%\' and id in (%); update platform_schema.reports_wot set accounting_export_summary = \'{}\' where org_id = \'%\' and id in (select report->>\'id\' from platform_schema.expenses_rov where org_id = \'%\' and id in (%));', _fyle_org_id, expense_ids, _fyle_org_id, _fyle_org_id, expense_ids;

RETURN;
END
$$;


ALTER FUNCTION public.delete_workspace(_workspace_id integer) OWNER TO postgres;

--
-- Name: json_diff(jsonb, jsonb); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.json_diff(left_json jsonb, right_json jsonb) RETURNS jsonb
    LANGUAGE sql
    AS $$
    SELECT jsonb_object_agg(left_table.key, jsonb_build_array(left_table.value, right_table.value)) FROM
        ( SELECT key, value FROM jsonb_each(left_json) ) left_table LEFT OUTER JOIN
        ( SELECT key, value FROM jsonb_each(right_json) ) right_table ON left_table.key = right_table.key
    WHERE left_table.value != right_table.value OR right_table.key IS NULL;
$$;


ALTER FUNCTION public.json_diff(left_json jsonb, right_json jsonb) OWNER TO postgres;

--
-- Name: log_delete_event(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.log_delete_event() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE difference jsonb;
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO update_logs(table_name, old_data, operation_type, workspace_id)
        VALUES (TG_TABLE_NAME, to_jsonb(OLD), 'DELETE', OLD.workspace_id);
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.log_delete_event() OWNER TO postgres;

--
-- Name: log_update_event(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.log_update_event() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    difference jsonb;
    key_count int;
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        difference := json_diff(to_jsonb(OLD), to_jsonb(NEW));

        -- Count the number of keys in the difference JSONB object
        SELECT COUNT(*)
        INTO key_count
        FROM jsonb_each_text(difference);

        -- If difference has only the key updated_at, then insert into update_logs
        IF TG_TABLE_NAME = 'expenses' THEN
            IF (difference ? 'accounting_export_summary') THEN
                INSERT INTO update_logs(table_name, old_data, new_data, difference, workspace_id)
                VALUES (TG_TABLE_NAME, to_jsonb(OLD), to_jsonb(NEW), difference, OLD.workspace_id);
            END IF;
        ELSE
            IF NOT (key_count = 1 AND difference ? 'updated_at') THEN
                INSERT INTO update_logs(table_name, old_data, new_data, difference, workspace_id)
                VALUES (TG_TABLE_NAME, to_jsonb(OLD), to_jsonb(NEW), difference, OLD.workspace_id);
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.log_update_event() OWNER TO postgres;

--
-- Name: re_export_expenses_intacct(integer, integer[], boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.re_export_expenses_intacct(_workspace_id integer, _expense_group_ids integer[], trigger_export boolean DEFAULT false) RETURNS void
    LANGUAGE plpgsql
    AS $$

DECLARE
  	rcount integer;
	temp_expenses integer[];
	local_expense_group_ids integer[];
	_fyle_org_id text;
	expense_ids text;
BEGIN
  RAISE NOTICE 'Starting to delete exported entries from workspace % ', _workspace_id;

local_expense_group_ids := _expense_group_ids;

_fyle_org_id := (select fyle_org_id from workspaces where id = _workspace_id);

SELECT array_agg(expense_id) into temp_expenses from expense_groups_expenses where expensegroup_id in (SELECT unnest(local_expense_group_ids));

expense_ids := (
	select string_agg(format('%L', expense_id), ', ')
	from expenses
	where workspace_id = _workspace_id
	and id in (SELECT unnest(temp_expenses))
);

DELETE
	FROM task_logs WHERE workspace_id = _workspace_id AND status = 'COMPLETE' and expense_group_id in (SELECT unnest(local_expense_group_ids));
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % task_logs', rcount;

DELETE
	FROM errors
	where expense_group_id IN (SELECT unnest(local_expense_group_ids));
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % errors', rcount;

DELETE
	FROM bill_lineitems bl
	WHERE bl.bill_id IN (
		SELECT b.id FROM bills b WHERE b.expense_group_id IN (
			SELECT unnest(local_expense_group_ids)
		)
	);
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % bill_lineitems', rcount;

DELETE
	FROM bills WHERE expense_group_id IN (SELECT unnest(local_expense_group_ids));
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % bills', rcount;

DELETE
	FROM charge_card_transaction_lineitems ccpl
	WHERE ccpl.charge_card_transaction_id IN (
		SELECT ccp.id FROM charge_card_transactions ccp WHERE ccp.expense_group_id IN (
			SELECT unnest(local_expense_group_ids)
		)
	);
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % charge_card_transaction_lineitems', rcount;

DELETE
	FROM charge_card_transactions WHERE expense_group_id IN (SELECT unnest(local_expense_group_ids));
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % charge_card_transactions', rcount;

DELETE
	FROM journal_entry_lineitems jel
	WHERE jel.journal_entry_id IN (
		SELECT je.id FROM journal_entries je WHERE je.expense_group_id IN (
			SELECT unnest(local_expense_group_ids)
		)
	);
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % journal_entry_lineitems', rcount;

DELETE
	FROM journal_entries WHERE expense_group_id IN (SELECT unnest(local_expense_group_ids));
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % journal_entries', rcount;

DELETE
	FROM expense_report_lineitems cl
	WHERE cl.expense_report_id IN (
		SELECT cq.id FROM expense_reports cq WHERE cq.expense_group_id IN (
			SELECT unnest(local_expense_group_ids)
		)
	);
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % expense_report_lineitems', rcount;

DELETE
	FROM expense_reports WHERE expense_group_id IN (SELECT unnest(local_expense_group_ids));
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Deleted % expense_reports', rcount;

UPDATE
	expense_groups set exported_at = null, response_logs = null
	WHERE id in (SELECT unnest(local_expense_group_ids)) and workspace_id = _workspace_id and exported_at is not null;
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Updating % expense_groups and resetting exported_at, response_logs', rcount;

UPDATE
	expenses set accounting_export_summary = '{}'
	where id in (SELECT unnest(temp_expenses));
	GET DIAGNOSTICS rcount = ROW_COUNT;
	RAISE NOTICE 'Updating % expenses and resetting accounting_export_summary', rcount;

RAISE NOTICE E'\n\n\nProd DB Queries to delete accounting export summaries:';
RAISE NOTICE E'rollback; begin; update platform_schema.expenses_wot set accounting_export_summary = \'{}\' where org_id = \'%\' and id in (%); update platform_schema.reports_wot set accounting_export_summary = \'{}\' where org_id = \'%\' and id in (select report->>\'id\' from platform_schema.expenses_rov where org_id = \'%\' and id in (%));', _fyle_org_id, expense_ids, _fyle_org_id, _fyle_org_id, expense_ids;

IF trigger_export THEN
    UPDATE django_q_schedule
        SET next_run = now() + INTERVAL '35 sec'
        WHERE args = _workspace_id::text and func = 'apps.workspaces.tasks.run_sync_schedule';

        GET DIAGNOSTICS rcount = ROW_COUNT;

        IF rcount > 0 THEN
            RAISE NOTICE 'Updated % schedule', rcount;
        ELSE
            RAISE NOTICE 'Schedule not updated since it doesnt exist';
        END IF;
END IF;

RETURN;
END
$$;


ALTER FUNCTION public.re_export_expenses_intacct(_workspace_id integer, _expense_group_ids integer[], trigger_export boolean) OWNER TO postgres;

--
-- Name: reset_location_entity_without_clearing_past_exports(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.reset_location_entity_without_clearing_past_exports(_workspace_id integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    rcount integer;
BEGIN
    RAISE NOTICE 'Deleting data from workspace %', _workspace_id;

    DELETE
    FROM dependent_field_settings dfs
    WHERE dfs.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % dependent_field_settings', rcount;

    DELETE
    FROM cost_types ct
    WHERE ct.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % cost_types', rcount;

    DELETE
    FROM location_entity_mappings lem
    WHERE lem.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % location_entity_mappings', rcount;

    DELETE
    FROM expense_fields ef
    WHERE ef.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % expense_fields', rcount;

    DELETE
    FROM errors e
    WHERE e.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % errors', rcount;

    DELETE
    FROM import_logs il
    WHERE il.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % import_logs', rcount;

    -- DELETE
    -- FROM task_logs tl
    -- WHERE tl.workspace_id = _workspace_id;
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % task_logs', rcount;

    -- DELETE
    -- FROM bill_lineitems bl
    -- WHERE bl.bill_id IN (
    --     SELECT b.id FROM bills b WHERE b.expense_group_id IN (
    --         SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    --     )
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % bill_lineitems', rcount;

    -- DELETE
    -- FROM bills b
    -- WHERE b.expense_group_id IN (
    --     SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % bills', rcount;

    -- DELETE
    -- FROM charge_card_transaction_lineitems cctl
    -- WHERE cctl.charge_card_transaction_id IN (
    --     SELECT cct.id FROM charge_card_transactions cct WHERE cct.expense_group_id IN (
    --         SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    --     )
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % charge_card_transaction_lineitems', rcount;

    -- DELETE
    -- FROM charge_card_transactions cct
    -- WHERE cct.expense_group_id IN (
    --     SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % charge_card_transactions', rcount;

    -- DELETE
    -- FROM journal_entry_lineitems jel
    -- WHERE jel.journal_entry_id IN (
    --     SELECT je.id FROM journal_entries je WHERE je.expense_group_id IN (
    --         SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    --     )
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % journal_entry_lineitems', rcount;

    -- DELETE
    -- FROM journal_entries je
    -- WHERE je.expense_group_id IN (
    --     SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % journal_entries', rcount;

    -- DELETE
    -- FROM expense_report_lineitems erl
    -- WHERE erl.expense_report_id IN (
    --     SELECT er.id FROM expense_reports er WHERE er.expense_group_id IN (
    --         SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    --     )
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % expense_report_lineitems', rcount;

        -- DELETE
        -- FROM expense_reports er
        -- WHERE er.expense_group_id IN (
        --     SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
        -- );
        -- GET DIAGNOSTICS rcount = ROW_COUNT;
        -- RAISE NOTICE 'Deleted % expense_reports', rcount;

    -- DELETE
    -- FROM ap_payment_lineitems apl
    -- WHERE apl.ap_payment_id IN (
    --     SELECT ap.id FROM ap_payments ap WHERE ap.expense_group_id IN (
    --         SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    --     )
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % ap_payment_lineitems', rcount;

    -- DELETE
    -- FROM ap_payments ap
    -- WHERE ap.expense_group_id IN (
    --     SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % ap_payments', rcount;

    -- DELETE
    -- FROM sage_intacct_reimbursement_lineitems sirl
    -- WHERE sirl.sage_intacct_reimbursement_id IN (
    --     SELECT sir.id FROM sage_intacct_reimbursements sir WHERE sir.expense_group_id IN (
    --         SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    --     )
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % sage_intacct_reimbursement_lineitems', rcount;

    -- DELETE
    -- FROM sage_intacct_reimbursements sir
    -- WHERE sir.expense_group_id IN (
    --     SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % sage_intacct_reimbursements', rcount;

    -- DELETE
    -- FROM reimbursements r
    -- WHERE r.workspace_id = _workspace_id;
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % reimbursements', rcount;

    -- DELETE
    -- FROM expenses e
    -- WHERE e.id IN (
    --     SELECT expense_id FROM expense_groups_expenses ege WHERE ege.expensegroup_id IN (
    --         SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    --     )
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % expenses', rcount;

    -- DELETE
    -- FROM expenses
    -- WHERE is_skipped=true and org_id in (SELECT fyle_org_id FROM workspaces WHERE id=_workspace_id);
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % skipped expenses', rcount;

    -- DELETE
    -- FROM expense_groups_expenses ege
    -- WHERE ege.expensegroup_id IN (
    --     SELECT eg.id FROM expense_groups eg WHERE eg.workspace_id = _workspace_id
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % expense_groups_expenses', rcount;

    -- DELETE
    -- FROM expense_groups eg
    -- WHERE eg.workspace_id = _workspace_id;
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % expense_groups', rcount;

    DELETE
    FROM mappings m
    WHERE m.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % mappings', rcount;

    DELETE
    FROM employee_mappings em
    WHERE em.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % employee_mappings', rcount;

    DELETE
    FROM category_mappings cm
    WHERE cm.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % category_mappings', rcount;

    DELETE
    FROM mapping_settings ms
    WHERE ms.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % mapping_settings', rcount;

    DELETE
    FROM general_mappings gm
    WHERE gm.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % general_mappings', rcount;

    DELETE
    FROM configurations c
    WHERE c.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % configurations', rcount;

    -- DELETE
    -- FROM expense_group_settings egs
    -- WHERE egs.workspace_id = _workspace_id;
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % expense_group_settings', rcount;

    -- DELETE
    -- FROM fyle_credentials fc
    -- WHERE fc.workspace_id = _workspace_id;
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % fyle_credentials', rcount;

    -- DELETE
    -- FROM sage_intacct_credentials sic
    -- WHERE sic.workspace_id = _workspace_id;
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % sage_intacct_credentials', rcount;

    DELETE
    FROM expense_attributes ea
    WHERE ea.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % expense_attributes', rcount;

    DELETE
    FROM expense_filters ef
    WHERE ef.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % expense_filters', rcount;

    DELETE
    FROM destination_attributes da
    WHERE da.workspace_id = _workspace_id and attribute_type != 'LOCATION_ENTITY';
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % destination_attributes', rcount;

    DELETE
    FROM workspace_schedules wsch
    WHERE wsch.workspace_id = _workspace_id;
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % workspace_schedules', rcount;

    -- DELETE
    -- FROM last_export_details led
    -- WHERE led.workspace_id = _workspace_id;
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % last_export_details', rcount;

    DELETE
    FROM django_q_schedule dqs
    WHERE dqs.args = _workspace_id::varchar(255);
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Deleted % django_q_schedule', rcount;

    -- DELETE
    -- FROM auth_tokens aut
    -- WHERE aut.user_id IN (
    --     SELECT u.id FROM users u WHERE u.id IN (
    --         SELECT wu.user_id FROM workspaces_user wu WHERE workspace_id = _workspace_id
    --     )
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % auth_tokens', rcount;

    -- DELETE
    -- FROM workspaces_user wu
    -- WHERE workspace_id = _workspace_id;
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % workspaces_user', rcount;

    -- DELETE
    -- FROM users u
    -- WHERE u.id IN (
    --     SELECT wu.user_id FROM workspaces_user wu WHERE workspace_id = _workspace_id
    -- );
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % users', rcount;

    -- DELETE
    -- FROM workspaces w
    -- WHERE w.id = _workspace_id;
    -- GET DIAGNOSTICS rcount = ROW_COUNT;
    -- RAISE NOTICE 'Deleted % workspaces', rcount;

    UPDATE workspaces
    set onboarding_state = 'CONNECTION', source_synced_at = null, destination_synced_at = null where id = _workspace_id;

    UPDATE last_export_details
    SET failed_expense_groups_count = null
    WHERE workspace_id = _workspace_id;

RETURN;
END
$$;


ALTER FUNCTION public.reset_location_entity_without_clearing_past_exports(_workspace_id integer) OWNER TO postgres;

--
-- Name: trigger_auto_import(character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trigger_auto_import(_workspace_id character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    rcount integer;
BEGIN
    UPDATE django_q_schedule
    SET next_run = now() + INTERVAL '35 sec'
    WHERE args = _workspace_id and func = 'apps.mappings.tasks.construct_tasks_and_chain_import_fields_to_fyle';

    GET DIAGNOSTICS rcount = ROW_COUNT;

    IF rcount > 0 THEN
        RAISE NOTICE 'Updated % schedule', rcount;
    ELSE
        RAISE NOTICE 'Schedule not updated since it doesnt exist';
    END IF;

RETURN;
END
$$;


ALTER FUNCTION public.trigger_auto_import(_workspace_id character varying) OWNER TO postgres;

--
-- Name: trigger_auto_import_export(character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trigger_auto_import_export(_workspace_id character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    rcount integer;
BEGIN
    UPDATE django_q_schedule
    SET next_run = now() + INTERVAL '35 sec'
    WHERE args = _workspace_id and func = 'apps.workspaces.tasks.run_sync_schedule';

    GET DIAGNOSTICS rcount = ROW_COUNT;

    IF rcount > 0 THEN
        RAISE NOTICE 'Updated % schedule', rcount;
    ELSE
        RAISE NOTICE 'Schedule not updated since it doesnt exist';
    END IF;

    update errors set updated_at = now() - interval '25 hours' where is_resolved = 'f' and workspace_id = NULLIF(_workspace_id, '')::int and repetition_count > 100;

RETURN;
END
$$;


ALTER FUNCTION public.trigger_auto_import_export(_workspace_id character varying) OWNER TO postgres;

--
-- Name: update_in_progress_tasks_to_failed(integer[]); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_in_progress_tasks_to_failed(_expense_group_ids integer[]) RETURNS void
    LANGUAGE plpgsql
    AS $$

DECLARE
  rcount integer;

BEGIN
    RAISE NOTICE 'Updating in progress tasks to failed for expense groups % ', _expense_group_ids;

UPDATE
    task_logs SET status = 'FAILED' WHERE status in ('ENQUEUED', 'IN_PROGRESS') and expense_group_id in (SELECT unnest(_expense_group_ids));
    GET DIAGNOSTICS rcount = ROW_COUNT;
    RAISE NOTICE 'Updated % task_logs', rcount;

RETURN;
END
$$;


ALTER FUNCTION public.update_in_progress_tasks_to_failed(_expense_group_ids integer[]) OWNER TO postgres;

--
-- Name: ws_email(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.ws_email(_workspace_id integer) RETURNS TABLE(workspace_id integer, workspace_name character varying, email character varying)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  RETURN QUERY
  select w.id as workspace_id, w.name as workspace_name, u.email as email from workspaces w
    left join workspaces_user wu on wu.workspace_id = w.id
    left join users u on wu.user_id = u.id
    where w.id = _workspace_id;
END;
$$;


ALTER FUNCTION public.ws_email(_workspace_id integer) OWNER TO postgres;

--
-- Name: ws_org_id(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.ws_org_id(_org_id text) RETURNS TABLE(workspace_id integer, workspace_org_id character varying, workspace_name character varying)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  RETURN QUERY
  select id as workspace_id, fyle_org_id as workspace_org_id, name as workspace_name
  from workspaces where fyle_org_id = _org_id;
END;
$$;


ALTER FUNCTION public.ws_org_id(_org_id text) OWNER TO postgres;

--
-- Name: ws_search(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.ws_search(_name text) RETURNS TABLE(workspace_id integer, workspace_org_id character varying, workspace_name character varying)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  RETURN QUERY
  select id as workspace_id, fyle_org_id as workspace_org_id, name as workspace_name
  from workspaces where name ilike '%' || _name || '%';
END;
$$;


ALTER FUNCTION public.ws_search(_name text) OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: configurations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.configurations (
    id integer NOT NULL,
    reimbursable_expenses_object character varying(50),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    corporate_credit_card_expenses_object character varying(50),
    import_projects boolean NOT NULL,
    sync_fyle_to_sage_intacct_payments boolean NOT NULL,
    sync_sage_intacct_to_fyle_payments boolean NOT NULL,
    auto_map_employees character varying(50),
    import_categories boolean NOT NULL,
    auto_create_destination_entity boolean NOT NULL,
    memo_structure character varying(100)[] NOT NULL,
    import_tax_codes boolean,
    change_accounting_period boolean NOT NULL,
    import_vendors_as_merchants boolean NOT NULL,
    employee_field_mapping character varying(50),
    use_merchant_in_journal_line boolean NOT NULL,
    is_journal_credit_billable boolean NOT NULL,
    auto_create_merchants_as_vendors boolean NOT NULL,
    import_code_fields character varying(100)[] NOT NULL,
    created_by character varying(255),
    updated_by character varying(255),
    skip_accounting_export_summary_post boolean NOT NULL,
    je_single_credit_line boolean NOT NULL,
    top_level_memo_structure character varying(100)[] NOT NULL
);


ALTER TABLE public.configurations OWNER TO postgres;

--
-- Name: expense_groups_expenses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_groups_expenses (
    id integer NOT NULL,
    expensegroup_id integer NOT NULL,
    expense_id integer NOT NULL
);


ALTER TABLE public.expense_groups_expenses OWNER TO postgres;

--
-- Name: expenses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expenses (
    id integer NOT NULL,
    employee_email character varying(255) NOT NULL,
    category character varying(255),
    sub_category character varying(255),
    project character varying(255),
    expense_id character varying(255) NOT NULL,
    expense_number character varying(255) NOT NULL,
    claim_number character varying(255),
    amount double precision NOT NULL,
    currency character varying(5) NOT NULL,
    foreign_amount double precision,
    foreign_currency character varying(5),
    settlement_id character varying(255),
    reimbursable boolean NOT NULL,
    state character varying(255) NOT NULL,
    vendor character varying(255),
    cost_center character varying(255),
    purpose text,
    report_id character varying(255) NOT NULL,
    spent_at timestamp with time zone,
    approved_at timestamp with time zone,
    expense_created_at timestamp with time zone NOT NULL,
    expense_updated_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    fund_source character varying(255) NOT NULL,
    custom_properties jsonb,
    verified_at timestamp with time zone,
    billable boolean,
    paid_on_sage_intacct boolean NOT NULL,
    org_id character varying(255),
    tax_amount double precision,
    tax_group_id character varying(255),
    file_ids character varying(255)[],
    payment_number character varying(55),
    corporate_card_id character varying(255),
    is_skipped boolean,
    report_title text,
    posted_at timestamp with time zone,
    employee_name character varying(255),
    accounting_export_summary jsonb NOT NULL,
    previous_export_state character varying(255),
    workspace_id integer,
    paid_on_fyle boolean NOT NULL,
    bank_transaction_id character varying(255),
    is_posted_at_null boolean NOT NULL,
    masked_corporate_card_number character varying(255),
    imported_from character varying(255)
);


ALTER TABLE public.expenses OWNER TO postgres;

--
-- Name: prod_workspaces_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.prod_workspaces_view AS
SELECT
    NULL::integer AS id,
    NULL::character varying(255) AS name,
    NULL::character varying(255) AS fyle_org_id,
    NULL::timestamp with time zone AS last_synced_at,
    NULL::timestamp with time zone AS created_at,
    NULL::timestamp with time zone AS updated_at,
    NULL::timestamp with time zone AS destination_synced_at,
    NULL::timestamp with time zone AS source_synced_at,
    NULL::character varying(255) AS cluster_domain,
    NULL::timestamp with time zone AS ccc_last_synced_at,
    NULL::character varying(50) AS onboarding_state,
    NULL::character varying(2) AS app_version,
    NULL::character varying[] AS user_emails;


ALTER VIEW public.prod_workspaces_view OWNER TO postgres;

--
-- Name: task_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.task_logs (
    id integer NOT NULL,
    type character varying(50) NOT NULL,
    task_id character varying(255),
    status character varying(255) NOT NULL,
    detail jsonb,
    sage_intacct_errors jsonb,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    bill_id integer,
    expense_report_id integer,
    expense_group_id integer,
    workspace_id integer NOT NULL,
    charge_card_transaction_id integer,
    ap_payment_id integer,
    sage_intacct_reimbursement_id integer,
    journal_entry_id integer,
    supdoc_id character varying(255),
    is_retired boolean NOT NULL,
    triggered_by character varying(255),
    re_attempt_export boolean NOT NULL,
    is_attachment_upload_failed boolean NOT NULL
);


ALTER TABLE public.task_logs OWNER TO postgres;

--
-- Name: _direct_export_errored_expenses_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public._direct_export_errored_expenses_view AS
 WITH prod_workspace_ids AS (
         SELECT prod_workspaces_view.id
           FROM public.prod_workspaces_view
        ), errored_expenses_in_complete_state AS (
         SELECT count(*) AS complete_expenses_error_count
           FROM public.expenses
          WHERE ((expenses.workspace_id IN ( SELECT prod_workspace_ids.id
                   FROM prod_workspace_ids)) AND ((expenses.accounting_export_summary ->> 'state'::text) <> ALL (ARRAY['COMPLETE'::text, 'DELETED'::text])) AND (expenses.id IN ( SELECT expense_groups_expenses.expense_id
                   FROM public.expense_groups_expenses
                  WHERE (expense_groups_expenses.expensegroup_id IN ( SELECT task_logs.expense_group_id
                           FROM public.task_logs
                          WHERE (((task_logs.status)::text = 'COMPLETE'::text) AND (task_logs.workspace_id IN ( SELECT prod_workspace_ids.id
                                   FROM prod_workspace_ids))))))))
        ), errored_expenses_in_error_state AS (
         SELECT count(*) AS error_expenses_error_count
           FROM public.expenses
          WHERE ((expenses.workspace_id IN ( SELECT prod_workspace_ids.id
                   FROM prod_workspace_ids)) AND ((expenses.accounting_export_summary ->> 'state'::text) <> ALL (ARRAY['ERROR'::text, 'DELETED'::text])) AND (expenses.id IN ( SELECT expense_groups_expenses.expense_id
                   FROM public.expense_groups_expenses
                  WHERE (expense_groups_expenses.expensegroup_id IN ( SELECT task_logs.expense_group_id
                           FROM public.task_logs
                          WHERE (((task_logs.status)::text = ANY (ARRAY[('FAILED'::character varying)::text, ('FATAL'::character varying)::text])) AND (task_logs.workspace_id IN ( SELECT prod_workspace_ids.id
                                   FROM prod_workspace_ids))))))))
        ), errored_expenses_in_inprogress_state AS (
         SELECT count(*) AS in_progress_expenses_error_count
           FROM public.expenses
          WHERE ((expenses.workspace_id IN ( SELECT prod_workspace_ids.id
                   FROM prod_workspace_ids)) AND ((expenses.accounting_export_summary ->> 'state'::text) <> ALL (ARRAY['IN_PROGRESS'::text, 'DELETED'::text])) AND (expenses.id IN ( SELECT expense_groups_expenses.expense_id
                   FROM public.expense_groups_expenses
                  WHERE (expense_groups_expenses.expensegroup_id IN ( SELECT task_logs.expense_group_id
                           FROM public.task_logs
                          WHERE (((task_logs.status)::text = 'IN_PROGRESS'::text) AND (task_logs.workspace_id IN ( SELECT prod_workspace_ids.id
                                   FROM prod_workspace_ids))))))))
        ), not_synced_to_platform AS (
         SELECT count(*) AS not_synced_expenses_count
           FROM (public.expenses e
             JOIN public.configurations c ON ((e.workspace_id = c.workspace_id)))
          WHERE ((e.workspace_id IN ( SELECT prod_workspace_ids.id
                   FROM prod_workspace_ids)) AND ((e.accounting_export_summary ->> 'synced'::text) = 'false'::text) AND (c.skip_accounting_export_summary_post = false))
        )
 SELECT errored_expenses_in_complete_state.complete_expenses_error_count,
    errored_expenses_in_error_state.error_expenses_error_count,
    errored_expenses_in_inprogress_state.in_progress_expenses_error_count,
    not_synced_to_platform.not_synced_expenses_count
   FROM errored_expenses_in_complete_state,
    errored_expenses_in_error_state,
    errored_expenses_in_inprogress_state,
    not_synced_to_platform;


ALTER VIEW public._direct_export_errored_expenses_view OWNER TO postgres;

--
-- Name: _django_queue_fatal_tasks_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public._django_queue_fatal_tasks_view AS
 SELECT 'FATAL'::text AS status,
    COALESCE(count(*), (0)::bigint) AS count
   FROM public.task_logs
  WHERE ((task_logs.workspace_id IN ( SELECT prod_workspaces_view.id
           FROM public.prod_workspaces_view)) AND ((task_logs.status)::text = 'FATAL'::text));


ALTER VIEW public._django_queue_fatal_tasks_view OWNER TO postgres;

--
-- Name: _django_queue_in_progress_tasks_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public._django_queue_in_progress_tasks_view AS
 SELECT 'IN_PROGRESS, ENQUEUED'::text AS status,
    COALESCE(count(*), (0)::bigint) AS count
   FROM public.task_logs
  WHERE ((task_logs.workspace_id IN ( SELECT prod_workspaces_view.id
           FROM public.prod_workspaces_view)) AND ((task_logs.status)::text = ANY (ARRAY[('IN_PROGRESS'::character varying)::text, ('ENQUEUED'::character varying)::text])));


ALTER VIEW public._django_queue_in_progress_tasks_view OWNER TO postgres;

--
-- Name: import_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.import_logs (
    id integer NOT NULL,
    attribute_type character varying(150) NOT NULL,
    status character varying(255),
    error_log jsonb NOT NULL,
    total_batches_count integer NOT NULL,
    processed_batches_count integer NOT NULL,
    last_successful_run_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.import_logs OWNER TO postgres;

--
-- Name: _import_logs_fatal_failed_in_progress_tasks_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public._import_logs_fatal_failed_in_progress_tasks_view AS
 SELECT count(*) AS log_count,
    import_logs.status,
    current_database() AS database
   FROM public.import_logs
  WHERE (((import_logs.status)::text = ANY (ARRAY[('IN_PROGRESS'::character varying)::text, ('FATAL'::character varying)::text, ('FAILED'::character varying)::text])) AND (import_logs.workspace_id IN ( SELECT prod_workspaces_view.id
           FROM public.prod_workspaces_view)) AND ((import_logs.error_log)::text !~~* '%Token%'::text) AND ((import_logs.error_log)::text !~~* '%tenant%'::text) AND (import_logs.updated_at < (now() - '00:45:00'::interval)))
  GROUP BY import_logs.status;


ALTER VIEW public._import_logs_fatal_failed_in_progress_tasks_view OWNER TO postgres;

--
-- Name: ap_payment_lineitems; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ap_payment_lineitems (
    id integer NOT NULL,
    amount double precision NOT NULL,
    record_key character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    ap_payment_id integer NOT NULL
);


ALTER TABLE public.ap_payment_lineitems OWNER TO postgres;

--
-- Name: ap_payment_lineitems_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ap_payment_lineitems_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ap_payment_lineitems_id_seq OWNER TO postgres;

--
-- Name: ap_payment_lineitems_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ap_payment_lineitems_id_seq OWNED BY public.ap_payment_lineitems.id;


--
-- Name: ap_payments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ap_payments (
    id integer NOT NULL,
    payment_account_id character varying(255) NOT NULL,
    vendor_id character varying(255) NOT NULL,
    description text NOT NULL,
    currency character varying(255) NOT NULL,
    created_at date NOT NULL,
    updated_at date NOT NULL,
    expense_group_id integer NOT NULL
);


ALTER TABLE public.ap_payments OWNER TO postgres;

--
-- Name: ap_payments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ap_payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ap_payments_id_seq OWNER TO postgres;

--
-- Name: ap_payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ap_payments_id_seq OWNED BY public.ap_payments.id;


--
-- Name: auth_cache; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_cache (
    cache_key character varying(255) NOT NULL,
    value text NOT NULL,
    expires timestamp with time zone NOT NULL
);


ALTER TABLE public.auth_cache OWNER TO postgres;

--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO postgres;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.auth_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auth_group_id_seq OWNER TO postgres;

--
-- Name: auth_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.auth_group_id_seq OWNED BY public.auth_group.id;


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group_permissions (
    id integer NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO postgres;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.auth_group_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auth_group_permissions_id_seq OWNER TO postgres;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.auth_group_permissions_id_seq OWNED BY public.auth_group_permissions.id;


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO postgres;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.auth_permission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auth_permission_id_seq OWNER TO postgres;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.auth_permission_id_seq OWNED BY public.auth_permission.id;


--
-- Name: auth_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_tokens (
    id integer NOT NULL,
    refresh_token text NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.auth_tokens OWNER TO postgres;

--
-- Name: bill_lineitems; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bill_lineitems (
    id integer NOT NULL,
    expense_type_id character varying(255),
    gl_account_number character varying(255),
    project_id character varying(255),
    location_id character varying(255),
    department_id character varying(255),
    memo text,
    amount double precision NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    bill_id integer NOT NULL,
    expense_id integer NOT NULL,
    billable boolean,
    customer_id character varying(255),
    item_id character varying(255),
    user_defined_dimensions jsonb,
    class_id character varying(255),
    tax_amount double precision,
    tax_code character varying(255),
    cost_type_id character varying(255),
    task_id character varying(255),
    allocation_id character varying(255)
);


ALTER TABLE public.bill_lineitems OWNER TO postgres;

--
-- Name: bills; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bills (
    id integer NOT NULL,
    vendor_id character varying(255) NOT NULL,
    description text NOT NULL,
    supdoc_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    expense_group_id integer NOT NULL,
    memo text,
    transaction_date timestamp with time zone,
    paid_on_sage_intacct boolean NOT NULL,
    payment_synced boolean NOT NULL,
    currency character varying(5) NOT NULL,
    is_retired boolean NOT NULL
);


ALTER TABLE public.bills OWNER TO postgres;

--
-- Name: category_mappings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.category_mappings (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    destination_account_id integer,
    destination_expense_head_id integer,
    source_category_id integer NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.category_mappings OWNER TO postgres;

--
-- Name: category_mappings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.category_mappings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.category_mappings_id_seq OWNER TO postgres;

--
-- Name: category_mappings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.category_mappings_id_seq OWNED BY public.category_mappings.id;


--
-- Name: charge_card_transaction_lineitems; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.charge_card_transaction_lineitems (
    id integer NOT NULL,
    gl_account_number character varying(255),
    project_id character varying(255),
    location_id character varying(255),
    department_id character varying(255),
    amount double precision NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    charge_card_transaction_id integer NOT NULL,
    expense_id integer NOT NULL,
    memo text,
    customer_id character varying(255),
    item_id character varying(255),
    class_id character varying(255),
    tax_amount double precision,
    tax_code character varying(255),
    cost_type_id character varying(255),
    task_id character varying(255),
    user_defined_dimensions jsonb,
    billable boolean,
    vendor_id character varying(255)
);


ALTER TABLE public.charge_card_transaction_lineitems OWNER TO postgres;

--
-- Name: charge_card_transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.charge_card_transactions (
    id integer NOT NULL,
    charge_card_id character varying(255) NOT NULL,
    description text NOT NULL,
    supdoc_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    expense_group_id integer NOT NULL,
    memo text,
    transaction_date timestamp with time zone,
    currency character varying(5) NOT NULL,
    reference_no character varying(255) NOT NULL,
    vendor_id character varying(255) NOT NULL,
    payee character varying(255)
);


ALTER TABLE public.charge_card_transactions OWNER TO postgres;

--
-- Name: cost_codes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cost_codes (
    id integer NOT NULL,
    task_id character varying(255),
    task_name character varying(255),
    project_id character varying(255),
    project_name character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.cost_codes OWNER TO postgres;

--
-- Name: cost_codes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.cost_codes ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.cost_codes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cost_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cost_types (
    id integer NOT NULL,
    record_number character varying(255) NOT NULL,
    project_key character varying(255) NOT NULL,
    project_id character varying(255) NOT NULL,
    project_name character varying(255) NOT NULL,
    task_key character varying(255) NOT NULL,
    task_id character varying(255) NOT NULL,
    status character varying(255),
    task_name character varying(255) NOT NULL,
    cost_type_id character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    when_created character varying(255),
    when_modified character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    is_imported boolean NOT NULL
);


ALTER TABLE public.cost_types OWNER TO postgres;

--
-- Name: cost_types_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.cost_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cost_types_id_seq OWNER TO postgres;

--
-- Name: cost_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.cost_types_id_seq OWNED BY public.cost_types.id;


--
-- Name: dependent_field_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dependent_field_settings (
    id integer NOT NULL,
    is_import_enabled boolean NOT NULL,
    project_field_id integer NOT NULL,
    cost_code_field_name character varying(255) NOT NULL,
    cost_code_field_id integer NOT NULL,
    cost_type_field_name character varying(255),
    cost_type_field_id integer,
    last_successful_import_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    cost_code_placeholder text,
    cost_type_placeholder text,
    last_synced_at timestamp with time zone,
    is_cost_type_import_enabled boolean NOT NULL
);


ALTER TABLE public.dependent_field_settings OWNER TO postgres;

--
-- Name: dependent_fields_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dependent_fields_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dependent_fields_id_seq OWNER TO postgres;

--
-- Name: dependent_fields_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dependent_fields_id_seq OWNED BY public.dependent_field_settings.id;


--
-- Name: destination_attributes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.destination_attributes (
    id integer NOT NULL,
    attribute_type character varying(255) NOT NULL,
    display_name character varying(255) NOT NULL,
    value character varying(255) NOT NULL,
    destination_id character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    active boolean,
    detail jsonb,
    auto_created boolean NOT NULL,
    code character varying(255)
);


ALTER TABLE public.destination_attributes OWNER TO postgres;

--
-- Name: dimension_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dimension_details (
    id integer NOT NULL,
    attribute_type character varying(255) NOT NULL,
    display_name character varying(255) NOT NULL,
    source_type character varying(100) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.dimension_details OWNER TO postgres;

--
-- Name: dimension_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.dimension_details ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.dimension_details_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: direct_export_errored_expenses_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.direct_export_errored_expenses_view AS
 WITH prod_workspace_ids AS (
         SELECT prod_workspaces_view.id
           FROM public.prod_workspaces_view
        ), errored_expenses_in_complete_state AS (
         SELECT count(*) AS complete_expenses_error_count
           FROM public.expenses
          WHERE ((expenses.workspace_id IN ( SELECT prod_workspace_ids.id
                   FROM prod_workspace_ids)) AND ((expenses.accounting_export_summary ->> 'state'::text) <> ALL (ARRAY['COMPLETE'::text, 'DELETED'::text])) AND (expenses.id IN ( SELECT expense_groups_expenses.expense_id
                   FROM public.expense_groups_expenses
                  WHERE (expense_groups_expenses.expensegroup_id IN ( SELECT task_logs.expense_group_id
                           FROM public.task_logs
                          WHERE (((task_logs.status)::text = 'COMPLETE'::text) AND (task_logs.workspace_id IN ( SELECT prod_workspace_ids.id
                                   FROM prod_workspace_ids)) AND (task_logs.updated_at > (now() - '1 day'::interval)) AND (task_logs.updated_at < (now() - '00:45:00'::interval))))))))
        ), errored_expenses_in_error_state AS (
         SELECT count(*) AS error_expenses_error_count
           FROM public.expenses
          WHERE ((expenses.workspace_id IN ( SELECT prod_workspace_ids.id
                   FROM prod_workspace_ids)) AND ((expenses.accounting_export_summary ->> 'state'::text) <> ALL (ARRAY['ERROR'::text, 'DELETED'::text])) AND (expenses.id IN ( SELECT expense_groups_expenses.expense_id
                   FROM public.expense_groups_expenses
                  WHERE (expense_groups_expenses.expensegroup_id IN ( SELECT task_logs.expense_group_id
                           FROM public.task_logs
                          WHERE (((task_logs.status)::text = ANY (ARRAY[('FAILED'::character varying)::text, ('FATAL'::character varying)::text])) AND (task_logs.workspace_id IN ( SELECT prod_workspace_ids.id
                                   FROM prod_workspace_ids)) AND (task_logs.updated_at > (now() - '1 day'::interval)) AND (task_logs.updated_at < (now() - '00:45:00'::interval))))))))
        ), errored_expenses_in_inprogress_state AS (
         SELECT count(*) AS in_progress_expenses_error_count
           FROM public.expenses
          WHERE ((expenses.workspace_id IN ( SELECT prod_workspace_ids.id
                   FROM prod_workspace_ids)) AND ((expenses.accounting_export_summary ->> 'state'::text) <> ALL (ARRAY['IN_PROGRESS'::text, 'DELETED'::text])) AND (expenses.id IN ( SELECT expense_groups_expenses.expense_id
                   FROM public.expense_groups_expenses
                  WHERE (expense_groups_expenses.expensegroup_id IN ( SELECT task_logs.expense_group_id
                           FROM public.task_logs
                          WHERE (((task_logs.status)::text = ANY (ARRAY[('IN_PROGRESS'::character varying)::text, ('ENQUEUED'::character varying)::text])) AND (task_logs.workspace_id IN ( SELECT prod_workspace_ids.id
                                   FROM prod_workspace_ids)) AND (task_logs.updated_at > (now() - '1 day'::interval)) AND (task_logs.updated_at < (now() - '00:45:00'::interval))))))))
        ), not_synced_to_platform AS (
         SELECT count(*) AS not_synced_expenses_count
           FROM (public.expenses e
             JOIN public.configurations c ON ((e.workspace_id = c.workspace_id)))
          WHERE ((e.workspace_id IN ( SELECT prod_workspace_ids.id
                   FROM prod_workspace_ids)) AND ((e.accounting_export_summary ->> 'synced'::text) = 'false'::text) AND (e.updated_at > (now() - '1 day'::interval)) AND (e.updated_at < (now() - '00:45:00'::interval)) AND (c.skip_accounting_export_summary_post = false))
        )
 SELECT errored_expenses_in_complete_state.complete_expenses_error_count,
    errored_expenses_in_error_state.error_expenses_error_count,
    errored_expenses_in_inprogress_state.in_progress_expenses_error_count,
    not_synced_to_platform.not_synced_expenses_count
   FROM errored_expenses_in_complete_state,
    errored_expenses_in_error_state,
    errored_expenses_in_inprogress_state,
    not_synced_to_platform;


ALTER VIEW public.direct_export_errored_expenses_view OWNER TO postgres;

--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO postgres;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.django_admin_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.django_admin_log_id_seq OWNER TO postgres;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.django_admin_log_id_seq OWNED BY public.django_admin_log.id;


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO postgres;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.django_content_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.django_content_type_id_seq OWNER TO postgres;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.django_content_type_id_seq OWNED BY public.django_content_type.id;


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_migrations (
    id integer NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO postgres;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.django_migrations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.django_migrations_id_seq OWNER TO postgres;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.django_migrations_id_seq OWNED BY public.django_migrations.id;


--
-- Name: django_q_ormq; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_q_ormq (
    id integer NOT NULL,
    key character varying(100) NOT NULL,
    payload text NOT NULL,
    lock timestamp with time zone
);


ALTER TABLE public.django_q_ormq OWNER TO postgres;

--
-- Name: django_q_ormq_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.django_q_ormq_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.django_q_ormq_id_seq OWNER TO postgres;

--
-- Name: django_q_ormq_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.django_q_ormq_id_seq OWNED BY public.django_q_ormq.id;


--
-- Name: django_q_schedule; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_q_schedule (
    id integer NOT NULL,
    func character varying(256) NOT NULL,
    hook character varying(256),
    args text,
    kwargs text,
    schedule_type character varying(2) NOT NULL,
    repeats integer NOT NULL,
    next_run timestamp with time zone,
    task character varying(100),
    name character varying(100),
    minutes smallint,
    cron character varying(100),
    cluster character varying(100),
    intended_date_kwarg character varying(100),
    CONSTRAINT django_q_schedule_minutes_check CHECK ((minutes >= 0))
);


ALTER TABLE public.django_q_schedule OWNER TO postgres;

--
-- Name: django_q_schedule_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.django_q_schedule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.django_q_schedule_id_seq OWNER TO postgres;

--
-- Name: django_q_schedule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.django_q_schedule_id_seq OWNED BY public.django_q_schedule.id;


--
-- Name: django_q_task; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_q_task (
    name character varying(100) NOT NULL,
    func character varying(256) NOT NULL,
    hook character varying(256),
    args text,
    kwargs text,
    result text,
    started timestamp with time zone NOT NULL,
    stopped timestamp with time zone NOT NULL,
    success boolean NOT NULL,
    id character varying(32) NOT NULL,
    "group" character varying(100),
    attempt_count integer NOT NULL,
    cluster character varying(100)
);


ALTER TABLE public.django_q_task OWNER TO postgres;

--
-- Name: django_queue_fatal_tasks_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.django_queue_fatal_tasks_view AS
 SELECT 'FATAL'::text AS status,
    COALESCE(count(*), (0)::bigint) AS count
   FROM public.task_logs
  WHERE ((task_logs.workspace_id IN ( SELECT prod_workspaces_view.id
           FROM public.prod_workspaces_view)) AND ((task_logs.status)::text = 'FATAL'::text) AND ((task_logs.updated_at >= (now() - '24:00:00'::interval)) AND (task_logs.updated_at <= (now() - '00:30:00'::interval))));


ALTER VIEW public.django_queue_fatal_tasks_view OWNER TO postgres;

--
-- Name: django_queue_in_progress_tasks_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.django_queue_in_progress_tasks_view AS
 SELECT 'IN_PROGRESS, ENQUEUED'::text AS status,
    COALESCE(count(*), (0)::bigint) AS count
   FROM public.task_logs
  WHERE ((task_logs.workspace_id IN ( SELECT prod_workspaces_view.id
           FROM public.prod_workspaces_view)) AND ((task_logs.status)::text = ANY (ARRAY[('IN_PROGRESS'::character varying)::text, ('ENQUEUED'::character varying)::text])) AND ((task_logs.updated_at >= (now() - '24:00:00'::interval)) AND (task_logs.updated_at <= (now() - '00:30:00'::interval))));


ALTER VIEW public.django_queue_in_progress_tasks_view OWNER TO postgres;

--
-- Name: django_session; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO postgres;

--
-- Name: employee_mappings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.employee_mappings (
    id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    destination_card_account_id integer,
    destination_employee_id integer,
    destination_vendor_id integer,
    source_employee_id integer NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.employee_mappings OWNER TO postgres;

--
-- Name: employee_mappings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.employee_mappings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.employee_mappings_id_seq OWNER TO postgres;

--
-- Name: employee_mappings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.employee_mappings_id_seq OWNED BY public.employee_mappings.id;


--
-- Name: errors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.errors (
    id integer NOT NULL,
    type character varying(50) NOT NULL,
    is_resolved boolean NOT NULL,
    error_title character varying(255) NOT NULL,
    error_detail text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    expense_attribute_id integer,
    expense_group_id integer,
    workspace_id integer NOT NULL,
    article_link text,
    attribute_type character varying(255),
    is_parsed boolean NOT NULL,
    repetition_count integer NOT NULL,
    mapping_error_expense_group_ids integer[] NOT NULL
);


ALTER TABLE public.errors OWNER TO postgres;

--
-- Name: errors_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.errors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.errors_id_seq OWNER TO postgres;

--
-- Name: errors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.errors_id_seq OWNED BY public.errors.id;


--
-- Name: expense_attributes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_attributes (
    id integer NOT NULL,
    attribute_type character varying(255) NOT NULL,
    display_name character varying(255) NOT NULL,
    value character varying(1000) NOT NULL,
    source_id character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    active boolean,
    detail jsonb,
    auto_mapped boolean NOT NULL,
    auto_created boolean NOT NULL
);


ALTER TABLE public.expense_attributes OWNER TO postgres;

--
-- Name: expense_attributes_deletion_cache; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_attributes_deletion_cache (
    id integer NOT NULL,
    category_ids character varying(255)[] NOT NULL,
    project_ids character varying(255)[] NOT NULL,
    workspace_id integer NOT NULL,
    cost_center_ids character varying(255)[] NOT NULL,
    custom_field_list jsonb NOT NULL,
    merchant_list character varying(255)[] NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.expense_attributes_deletion_cache OWNER TO postgres;

--
-- Name: expense_attributes_deletion_cache_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.expense_attributes_deletion_cache_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.expense_attributes_deletion_cache_id_seq OWNER TO postgres;

--
-- Name: expense_attributes_deletion_cache_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.expense_attributes_deletion_cache_id_seq OWNED BY public.expense_attributes_deletion_cache.id;


--
-- Name: expense_fields; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_fields (
    id integer NOT NULL,
    attribute_type character varying(255) NOT NULL,
    source_field_id integer NOT NULL,
    is_enabled boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.expense_fields OWNER TO postgres;

--
-- Name: expense_fields_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.expense_fields_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.expense_fields_id_seq OWNER TO postgres;

--
-- Name: expense_fields_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.expense_fields_id_seq OWNED BY public.expense_fields.id;


--
-- Name: expense_filters; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_filters (
    id integer NOT NULL,
    condition character varying(255) NOT NULL,
    operator character varying(255) NOT NULL,
    "values" character varying(255)[],
    rank integer NOT NULL,
    join_by character varying(3),
    is_custom boolean NOT NULL,
    custom_field_type character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.expense_filters OWNER TO postgres;

--
-- Name: expense_filters_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.expense_filters_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.expense_filters_id_seq OWNER TO postgres;

--
-- Name: expense_filters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.expense_filters_id_seq OWNED BY public.expense_filters.id;


--
-- Name: expense_group_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_group_settings (
    id integer NOT NULL,
    reimbursable_expense_group_fields character varying(100)[] NOT NULL,
    corporate_credit_card_expense_group_fields character varying(100)[] NOT NULL,
    expense_state character varying(100) NOT NULL,
    reimbursable_export_date_type character varying(100) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    ccc_export_date_type character varying(100) NOT NULL,
    ccc_expense_state character varying(100),
    split_expense_grouping character varying(100) NOT NULL,
    created_by character varying(255),
    updated_by character varying(255)
);


ALTER TABLE public.expense_group_settings OWNER TO postgres;

--
-- Name: expense_group_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.expense_group_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.expense_group_settings_id_seq OWNER TO postgres;

--
-- Name: expense_group_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.expense_group_settings_id_seq OWNED BY public.expense_group_settings.id;


--
-- Name: expense_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_groups (
    id integer NOT NULL,
    description jsonb,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    fund_source character varying(255) NOT NULL,
    exported_at timestamp with time zone,
    export_type character varying(50),
    employee_name character varying(100),
    response_logs jsonb,
    export_url character varying(255)
);


ALTER TABLE public.expense_groups OWNER TO postgres;

--
-- Name: expense_report_lineitems; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_report_lineitems (
    id integer NOT NULL,
    expense_type_id character varying(255),
    gl_account_number character varying(255),
    project_id character varying(255),
    location_id character varying(255),
    department_id character varying(255),
    memo text,
    amount double precision NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    expense_report_id integer NOT NULL,
    expense_id integer NOT NULL,
    transaction_date timestamp with time zone,
    billable boolean,
    customer_id character varying(255),
    item_id character varying(255),
    user_defined_dimensions jsonb,
    expense_payment_type character varying(255),
    class_id character varying(255),
    tax_amount double precision,
    tax_code character varying(255),
    cost_type_id character varying(255),
    task_id character varying(255),
    vendor_id character varying(255)
);


ALTER TABLE public.expense_report_lineitems OWNER TO postgres;

--
-- Name: expense_reports; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expense_reports (
    id integer NOT NULL,
    employee_id character varying(255) NOT NULL,
    description text NOT NULL,
    supdoc_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    expense_group_id integer NOT NULL,
    memo text,
    transaction_date timestamp with time zone,
    paid_on_sage_intacct boolean NOT NULL,
    payment_synced boolean NOT NULL,
    currency character varying(5) NOT NULL,
    is_retired boolean NOT NULL
);


ALTER TABLE public.expense_reports OWNER TO postgres;

--
-- Name: extended_category_mappings_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.extended_category_mappings_view AS
 SELECT ea.id AS expense_attribute_id,
    ea.attribute_type AS expense_attribute_attribute_type,
    ea.display_name AS expense_attribute_display_name,
    ea.value AS expense_attribute_value,
    ea.auto_mapped AS expense_attribute_auto_mapped,
    ea.auto_created AS expense_attribute_auto_created,
    ea.created_at AS expense_attribute_created_at,
    ea.updated_at AS expense_attribute_updated_at,
    ea.source_id AS expense_attribute_source_id,
    ea.detail AS expense_attribute_detail,
    ea.active AS expense_attribute_active,
    da.id AS destination_attribute_id,
    da.attribute_type AS destination_attribute_attribute_type,
    da.display_name AS destination_attribute_display_name,
    da.value AS destination_attribute_value,
    da.destination_id AS destination_attribute_destination_id,
    da.auto_created AS destination_attribute_auto_created,
    da.detail AS destination_attribute_detail,
    da.active AS destination_attribute_active,
    da.created_at AS destination_attribute_created_at,
    da.updated_at AS destination_attribute_updated_at,
    cm.workspace_id
   FROM (((public.category_mappings cm
     JOIN public.expense_attributes ea ON ((ea.id = cm.source_category_id)))
     JOIN public.destination_attributes da ON ((da.id = cm.destination_account_id)))
     JOIN public.destination_attributes da2 ON ((da2.id = cm.destination_expense_head_id)));


ALTER VIEW public.extended_category_mappings_view OWNER TO postgres;

--
-- Name: extended_employee_mappings_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.extended_employee_mappings_view AS
 SELECT ea.id AS expense_attribute_id,
    ea.attribute_type AS expense_attribute_attribute_type,
    ea.display_name AS expense_attribute_display_name,
    ea.value AS expense_attribute_value,
    ea.auto_mapped AS expense_attribute_auto_mapped,
    ea.auto_created AS expense_attribute_auto_created,
    ea.created_at AS expense_attribute_created_at,
    ea.updated_at AS expense_attribute_updated_at,
    ea.source_id AS expense_attribute_source_id,
    ea.detail AS expense_attribute_detail,
    ea.active AS expense_attribute_active,
    da.id AS destination_attribute_id,
    da.attribute_type AS destination_attribute_attribute_type,
    da.display_name AS destination_attribute_display_name,
    da.value AS destination_attribute_value,
    da.destination_id AS destination_attribute_destination_id,
    da.auto_created AS destination_attribute_auto_created,
    da.detail AS destination_attribute_detail,
    da.active AS destination_attribute_active,
    da.created_at AS destination_attribute_created_at,
    da.updated_at AS destination_attribute_updated_at,
    em.workspace_id
   FROM ((((public.employee_mappings em
     JOIN public.expense_attributes ea ON ((ea.id = em.source_employee_id)))
     JOIN public.destination_attributes da ON ((da.id = em.destination_employee_id)))
     JOIN public.destination_attributes da2 ON ((da2.id = em.destination_vendor_id)))
     JOIN public.destination_attributes da3 ON ((da3.id = em.destination_card_account_id)));


ALTER VIEW public.extended_employee_mappings_view OWNER TO postgres;

--
-- Name: extended_expenses_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.extended_expenses_view AS
 SELECT e.id,
    e.employee_email,
    e.category,
    e.sub_category,
    e.project,
    e.expense_id,
    e.expense_number,
    e.claim_number,
    e.amount,
    e.currency,
    e.foreign_amount,
    e.foreign_currency,
    e.settlement_id,
    e.reimbursable,
    e.state,
    e.vendor,
    e.cost_center,
    e.purpose,
    e.report_id,
    e.spent_at,
    e.approved_at,
    e.expense_created_at,
    e.expense_updated_at,
    e.created_at,
    e.updated_at,
    e.fund_source,
    e.custom_properties,
    e.verified_at,
    e.billable,
    e.paid_on_sage_intacct,
    e.org_id,
    e.tax_amount,
    e.tax_group_id,
    e.file_ids,
    e.payment_number,
    e.corporate_card_id,
    e.is_skipped,
    e.report_title,
    e.posted_at,
    e.employee_name,
    e.accounting_export_summary,
    e.previous_export_state,
    e.workspace_id,
    e.paid_on_fyle,
    e.bank_transaction_id,
    e.is_posted_at_null,
    e.masked_corporate_card_number,
    eg.id AS expense_group_id,
    eg.employee_name AS expense_group_employee_name,
    eg.export_url AS expense_group_export_url,
    eg.description AS expense_group_description,
    eg.created_at AS expense_group_created_at,
    eg.updated_at AS expense_group_updated_at,
    eg.workspace_id AS expense_group_workspace_id,
    eg.fund_source AS expense_group_fund_source,
    eg.exported_at AS expense_group_exported_at,
    eg.response_logs AS expense_group_response_logs
   FROM ((public.expenses e
     JOIN public.expense_groups_expenses ege ON ((ege.expense_id = e.id)))
     JOIN public.expense_groups eg ON ((eg.id = ege.expensegroup_id)));


ALTER VIEW public.extended_expenses_view OWNER TO postgres;

--
-- Name: mappings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mappings (
    id integer NOT NULL,
    source_type character varying(255) NOT NULL,
    destination_type character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    destination_id integer NOT NULL,
    source_id integer NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.mappings OWNER TO postgres;

--
-- Name: extended_mappings_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.extended_mappings_view AS
 SELECT ea.id AS expense_attribute_id,
    ea.attribute_type AS expense_attribute_attribute_type,
    ea.display_name AS expense_attribute_display_name,
    ea.value AS expense_attribute_value,
    ea.auto_mapped AS expense_attribute_auto_mapped,
    ea.auto_created AS expense_attribute_auto_created,
    ea.created_at AS expense_attribute_created_at,
    ea.updated_at AS expense_attribute_updated_at,
    ea.source_id AS expense_attribute_source_id,
    ea.detail AS expense_attribute_detail,
    ea.active AS expense_attribute_active,
    da.id AS destination_attribute_id,
    da.attribute_type AS destination_attribute_attribute_type,
    da.display_name AS destination_attribute_display_name,
    da.value AS destination_attribute_value,
    da.destination_id AS destination_attribute_destination_id,
    da.auto_created AS destination_attribute_auto_created,
    da.detail AS destination_attribute_detail,
    da.active AS destination_attribute_active,
    da.created_at AS destination_attribute_created_at,
    da.updated_at AS destination_attribute_updated_at,
    m.workspace_id
   FROM ((public.mappings m
     JOIN public.expense_attributes ea ON ((ea.id = m.source_id)))
     JOIN public.destination_attributes da ON ((da.id = m.destination_id)));


ALTER VIEW public.extended_mappings_view OWNER TO postgres;

--
-- Name: general_mappings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.general_mappings (
    id integer NOT NULL,
    default_location_name character varying(255),
    default_location_id character varying(255),
    default_department_name character varying(255),
    default_department_id character varying(255),
    default_project_name character varying(255),
    default_project_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    default_charge_card_name character varying(255),
    default_charge_card_id character varying(255),
    default_ccc_vendor_name character varying(255),
    default_ccc_vendor_id character varying(255),
    default_item_id character varying(255),
    default_item_name character varying(255),
    payment_account_id character varying(255),
    payment_account_name character varying(255),
    default_ccc_expense_payment_type_id character varying(255),
    default_ccc_expense_payment_type_name character varying(255),
    default_reimbursable_expense_payment_type_id character varying(255),
    default_reimbursable_expense_payment_type_name character varying(255),
    use_intacct_employee_departments boolean NOT NULL,
    use_intacct_employee_locations boolean NOT NULL,
    location_entity_id character varying(255),
    location_entity_name character varying(255),
    default_class_id character varying(255),
    default_class_name character varying(255),
    default_tax_code_id character varying(255),
    default_tax_code_name character varying(255),
    default_credit_card_id character varying(255),
    default_credit_card_name character varying(255),
    default_gl_account_id character varying(255),
    default_gl_account_name character varying(255),
    created_by character varying(255),
    updated_by character varying(255)
);


ALTER TABLE public.general_mappings OWNER TO postgres;

--
-- Name: last_export_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.last_export_details (
    id integer NOT NULL,
    last_exported_at timestamp with time zone,
    export_mode character varying(50),
    total_expense_groups_count integer,
    successful_expense_groups_count integer,
    failed_expense_groups_count integer,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    next_export_at timestamp with time zone,
    unmapped_card_count integer NOT NULL
);


ALTER TABLE public.last_export_details OWNER TO postgres;

--
-- Name: workspace_schedules; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workspace_schedules (
    id integer NOT NULL,
    enabled boolean NOT NULL,
    start_datetime timestamp with time zone,
    interval_hours integer,
    schedule_id integer,
    workspace_id integer NOT NULL,
    additional_email_options jsonb,
    emails_selected character varying(255)[],
    error_count integer,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    is_real_time_export_enabled boolean NOT NULL
);


ALTER TABLE public.workspace_schedules OWNER TO postgres;

--
-- Name: workspaces; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workspaces (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    fyle_org_id character varying(255) NOT NULL,
    last_synced_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    destination_synced_at timestamp with time zone,
    source_synced_at timestamp with time zone,
    cluster_domain character varying(255),
    ccc_last_synced_at timestamp with time zone,
    onboarding_state character varying(50),
    app_version character varying(2) NOT NULL
);


ALTER TABLE public.workspaces OWNER TO postgres;

--
-- Name: extended_settings_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.extended_settings_view AS
 SELECT row_to_json(w.*) AS workspaces,
    row_to_json(c.*) AS configurations,
    row_to_json(gm.*) AS general_mappings,
    row_to_json(ws.*) AS workspace_schedules,
    row_to_json(egs.*) AS expense_group_settings,
    row_to_json(led.*) AS last_export_details,
    w.fyle_org_id
   FROM (((((public.workspaces w
     LEFT JOIN public.configurations c ON ((w.id = c.workspace_id)))
     LEFT JOIN public.general_mappings gm ON ((gm.workspace_id = w.id)))
     LEFT JOIN public.workspace_schedules ws ON ((ws.workspace_id = w.id)))
     LEFT JOIN public.expense_group_settings egs ON ((egs.workspace_id = w.id)))
     LEFT JOIN public.last_export_details led ON ((led.workspace_id = w.id)));


ALTER VIEW public.extended_settings_view OWNER TO postgres;

--
-- Name: failed_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.failed_events (
    id integer NOT NULL,
    routing_key character varying(255) NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    error_traceback text,
    workspace_id integer,
    is_resolved boolean NOT NULL
);


ALTER TABLE public.failed_events OWNER TO postgres;

--
-- Name: failed_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.failed_events ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.failed_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: feature_configs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.feature_configs (
    id integer NOT NULL,
    export_via_rabbitmq boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    import_via_rabbitmq boolean NOT NULL,
    fyle_webhook_sync_enabled boolean NOT NULL,
    migrated_to_rest_api boolean NOT NULL
);


ALTER TABLE public.feature_configs OWNER TO postgres;

--
-- Name: feature_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.feature_configs ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.feature_configs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: fyle_accounting_mappings_destinationattribute_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_accounting_mappings_destinationattribute_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fyle_accounting_mappings_destinationattribute_id_seq OWNER TO postgres;

--
-- Name: fyle_accounting_mappings_destinationattribute_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_accounting_mappings_destinationattribute_id_seq OWNED BY public.destination_attributes.id;


--
-- Name: fyle_accounting_mappings_expenseattribute_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_accounting_mappings_expenseattribute_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fyle_accounting_mappings_expenseattribute_id_seq OWNER TO postgres;

--
-- Name: fyle_accounting_mappings_expenseattribute_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_accounting_mappings_expenseattribute_id_seq OWNED BY public.expense_attributes.id;


--
-- Name: fyle_accounting_mappings_mapping_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_accounting_mappings_mapping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fyle_accounting_mappings_mapping_id_seq OWNER TO postgres;

--
-- Name: fyle_accounting_mappings_mapping_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_accounting_mappings_mapping_id_seq OWNED BY public.mappings.id;


--
-- Name: mapping_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mapping_settings (
    id integer NOT NULL,
    source_field character varying(255) NOT NULL,
    destination_field character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    import_to_fyle boolean NOT NULL,
    is_custom boolean NOT NULL,
    source_placeholder text,
    expense_field_id integer,
    created_by character varying(255),
    updated_by character varying(255)
);


ALTER TABLE public.mapping_settings OWNER TO postgres;

--
-- Name: fyle_accounting_mappings_mappingsetting_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_accounting_mappings_mappingsetting_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fyle_accounting_mappings_mappingsetting_id_seq OWNER TO postgres;

--
-- Name: fyle_accounting_mappings_mappingsetting_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_accounting_mappings_mappingsetting_id_seq OWNED BY public.mapping_settings.id;


--
-- Name: fyle_credentials; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fyle_credentials (
    id integer NOT NULL,
    refresh_token text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    cluster_domain text
);


ALTER TABLE public.fyle_credentials OWNER TO postgres;

--
-- Name: fyle_expense_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_expense_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fyle_expense_id_seq OWNER TO postgres;

--
-- Name: fyle_expense_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_expense_id_seq OWNED BY public.expenses.id;


--
-- Name: fyle_expensegroup_expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_expensegroup_expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fyle_expensegroup_expenses_id_seq OWNER TO postgres;

--
-- Name: fyle_expensegroup_expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_expensegroup_expenses_id_seq OWNED BY public.expense_groups_expenses.id;


--
-- Name: fyle_expensegroup_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_expensegroup_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fyle_expensegroup_id_seq OWNER TO postgres;

--
-- Name: fyle_expensegroup_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_expensegroup_id_seq OWNED BY public.expense_groups.id;


--
-- Name: fyle_rest_auth_authtokens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fyle_rest_auth_authtokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fyle_rest_auth_authtokens_id_seq OWNER TO postgres;

--
-- Name: fyle_rest_auth_authtokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fyle_rest_auth_authtokens_id_seq OWNED BY public.auth_tokens.id;


--
-- Name: fyle_sync_timestamps; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fyle_sync_timestamps (
    id integer NOT NULL,
    category_synced_at timestamp with time zone,
    project_synced_at timestamp with time zone,
    cost_center_synced_at timestamp with time zone,
    employee_synced_at timestamp with time zone,
    expense_field_synced_at timestamp with time zone,
    corporate_card_synced_at timestamp with time zone,
    dependent_field_synced_at timestamp with time zone,
    tax_group_synced_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.fyle_sync_timestamps OWNER TO postgres;

--
-- Name: fyle_sync_timestamps_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.fyle_sync_timestamps ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.fyle_sync_timestamps_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: huge_export_failing_orgs_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.huge_export_failing_orgs_view AS
 SELECT last_export_details.workspace_id,
    last_export_details.failed_expense_groups_count AS count
   FROM public.last_export_details
  WHERE ((last_export_details.failed_expense_groups_count > 50) AND (last_export_details.workspace_id IN ( SELECT prod_workspaces_view.id
           FROM public.prod_workspaces_view)));


ALTER VIEW public.huge_export_failing_orgs_view OWNER TO postgres;

--
-- Name: huge_export_volume_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.huge_export_volume_view AS
 SELECT task_logs.workspace_id,
    count(*) AS count
   FROM public.task_logs
  WHERE (((task_logs.status)::text = ANY (ARRAY[('ENQUEUED'::character varying)::text, ('IN_PROGRESS'::character varying)::text])) AND ((task_logs.type)::text !~~* '%fetching%'::text) AND (task_logs.workspace_id IN ( SELECT prod_workspaces_view.id
           FROM public.prod_workspaces_view)) AND (task_logs.updated_at >= (now() - '1 day'::interval)))
  GROUP BY task_logs.workspace_id
 HAVING (count(*) > 500);


ALTER VIEW public.huge_export_volume_view OWNER TO postgres;

--
-- Name: import_logs_fatal_failed_in_progress_tasks_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.import_logs_fatal_failed_in_progress_tasks_view AS
 SELECT count(*) AS count,
    import_logs.status,
    current_database() AS database
   FROM public.import_logs
  WHERE (((import_logs.status)::text = ANY (ARRAY[('IN_PROGRESS'::character varying)::text, ('FATAL'::character varying)::text, ('FAILED'::character varying)::text])) AND (import_logs.workspace_id IN ( SELECT prod_workspaces_view.id
           FROM public.prod_workspaces_view)) AND (import_logs.updated_at > (now() - '1 day'::interval)) AND (import_logs.updated_at < (now() - '00:45:00'::interval)) AND ((import_logs.error_log)::text !~~* '%Token%'::text) AND ((import_logs.error_log)::text !~~* '%tenant%'::text))
  GROUP BY import_logs.status;


ALTER VIEW public.import_logs_fatal_failed_in_progress_tasks_view OWNER TO postgres;

--
-- Name: import_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.import_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.import_logs_id_seq OWNER TO postgres;

--
-- Name: import_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.import_logs_id_seq OWNED BY public.import_logs.id;


--
-- Name: inactive_workspaces_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.inactive_workspaces_view AS
 SELECT count(DISTINCT w.id) AS count,
    current_database() AS database
   FROM ((public.workspaces w
     JOIN public.last_export_details led ON ((w.id = led.workspace_id)))
     JOIN public.django_q_schedule dqs ON (((w.id)::text = dqs.args)))
  WHERE ((w.source_synced_at < (now() - '2 mons'::interval)) AND (w.destination_synced_at < (now() - '2 mons'::interval)) AND (w.last_synced_at < (now() - '2 mons'::interval)) AND (w.ccc_last_synced_at < (now() - '2 mons'::interval)) AND (led.last_exported_at < (now() - '2 mons'::interval)) AND (w.id IN ( SELECT prod_workspaces_view.id
           FROM public.prod_workspaces_view)));


ALTER VIEW public.inactive_workspaces_view OWNER TO postgres;

--
-- Name: intacct_sync_timestamps; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.intacct_sync_timestamps (
    id integer NOT NULL,
    account_synced_at timestamp with time zone,
    vendor_synced_at timestamp with time zone,
    customer_synced_at timestamp with time zone,
    class_synced_at timestamp with time zone,
    employee_synced_at timestamp with time zone,
    item_synced_at timestamp with time zone,
    location_synced_at timestamp with time zone,
    allocation_synced_at timestamp with time zone,
    tax_detail_synced_at timestamp with time zone,
    department_synced_at timestamp with time zone,
    project_synced_at timestamp with time zone,
    expense_type_synced_at timestamp with time zone,
    location_entity_synced_at timestamp with time zone,
    payment_account_synced_at timestamp with time zone,
    expense_payment_type_synced_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.intacct_sync_timestamps OWNER TO postgres;

--
-- Name: intacct_sync_timestamps_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.intacct_sync_timestamps ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.intacct_sync_timestamps_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: journal_entries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.journal_entries (
    id integer NOT NULL,
    description text NOT NULL,
    memo text,
    currency character varying(5) NOT NULL,
    supdoc_id character varying(255),
    transaction_date timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    expense_group_id integer NOT NULL
);


ALTER TABLE public.journal_entries OWNER TO postgres;

--
-- Name: journal_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.journal_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.journal_entries_id_seq OWNER TO postgres;

--
-- Name: journal_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.journal_entries_id_seq OWNED BY public.journal_entries.id;


--
-- Name: journal_entry_lineitems; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.journal_entry_lineitems (
    id integer NOT NULL,
    gl_account_number character varying(255),
    project_id character varying(255),
    location_id character varying(255),
    class_id character varying(255),
    department_id character varying(255),
    customer_id character varying(255),
    item_id character varying(255),
    memo text,
    user_defined_dimensions jsonb,
    amount double precision NOT NULL,
    billable boolean,
    transaction_date timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    expense_id integer NOT NULL,
    journal_entry_id integer NOT NULL,
    employee_id character varying(255),
    vendor_id character varying(255),
    tax_amount double precision,
    tax_code character varying(255),
    cost_type_id character varying(255),
    task_id character varying(255),
    allocation_id boolean
);


ALTER TABLE public.journal_entry_lineitems OWNER TO postgres;

--
-- Name: journal_entry_lineitems_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.journal_entry_lineitems_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.journal_entry_lineitems_id_seq OWNER TO postgres;

--
-- Name: journal_entry_lineitems_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.journal_entry_lineitems_id_seq OWNED BY public.journal_entry_lineitems.id;


--
-- Name: last_export_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.last_export_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.last_export_details_id_seq OWNER TO postgres;

--
-- Name: last_export_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.last_export_details_id_seq OWNED BY public.last_export_details.id;


--
-- Name: location_entity_mappings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.location_entity_mappings (
    id integer NOT NULL,
    location_entity_name character varying(255) NOT NULL,
    country_name character varying(255),
    destination_id character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.location_entity_mappings OWNER TO postgres;

--
-- Name: location_entity_mappings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.location_entity_mappings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.location_entity_mappings_id_seq OWNER TO postgres;

--
-- Name: location_entity_mappings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.location_entity_mappings_id_seq OWNED BY public.location_entity_mappings.id;


--
-- Name: mappings_generalmapping_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.mappings_generalmapping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.mappings_generalmapping_id_seq OWNER TO postgres;

--
-- Name: mappings_generalmapping_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.mappings_generalmapping_id_seq OWNED BY public.general_mappings.id;


--
-- Name: ormq_count_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.ormq_count_view AS
 SELECT count(*) AS count,
    current_database() AS database
   FROM public.django_q_ormq;


ALTER VIEW public.ormq_count_view OWNER TO postgres;

--
-- Name: prod_active_workspaces_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.prod_active_workspaces_view AS
SELECT
    NULL::integer AS id,
    NULL::character varying(255) AS name,
    NULL::character varying(255) AS fyle_org_id,
    NULL::timestamp with time zone AS last_synced_at,
    NULL::timestamp with time zone AS created_at,
    NULL::timestamp with time zone AS updated_at,
    NULL::timestamp with time zone AS destination_synced_at,
    NULL::timestamp with time zone AS source_synced_at,
    NULL::character varying(255) AS cluster_domain,
    NULL::timestamp with time zone AS ccc_last_synced_at,
    NULL::character varying(50) AS onboarding_state,
    NULL::character varying(2) AS app_version,
    NULL::character varying[] AS user_emails;


ALTER VIEW public.prod_active_workspaces_view OWNER TO postgres;

--
-- Name: product_advanced_settings_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.product_advanced_settings_view AS
 SELECT w.id AS workspace_id,
    w.name AS workspace_name,
    w.fyle_org_id AS workspace_org_id,
    c.change_accounting_period,
    c.sync_fyle_to_sage_intacct_payments,
    c.sync_sage_intacct_to_fyle_payments,
    c.auto_create_destination_entity,
    c.memo_structure,
    c.auto_create_merchants_as_vendors,
    gm.payment_account_name,
    gm.payment_account_id,
    gm.default_location_name,
    gm.default_location_id,
    gm.default_project_name,
    gm.default_project_id,
    gm.default_item_name,
    gm.default_item_id,
    gm.use_intacct_employee_departments,
    gm.use_intacct_employee_locations,
    ws.enabled AS schedule_enabled,
    ws.interval_hours AS schedule_interval_hours,
    ws.additional_email_options AS schedule_additional_email_options,
    ws.emails_selected AS schedule_emails_selected
   FROM (((public.workspaces w
     JOIN public.configurations c ON ((w.id = c.workspace_id)))
     JOIN public.general_mappings gm ON ((w.id = gm.workspace_id)))
     LEFT JOIN public.workspace_schedules ws ON ((w.id = ws.workspace_id)));


ALTER VIEW public.product_advanced_settings_view OWNER TO postgres;

--
-- Name: product_import_settings_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.product_import_settings_view AS
 SELECT w.id AS workspace_id,
    w.name AS workspace_name,
    w.fyle_org_id AS workspace_org_id,
    c.import_categories,
    c.import_tax_codes,
    c.import_vendors_as_merchants,
    c.import_code_fields,
    gm.default_tax_code_name,
    gm.default_tax_code_id,
    COALESCE(json_agg(json_build_object('source_field', ms.source_field, 'destination_field', ms.destination_field, 'import_to_fyle', ms.import_to_fyle, 'is_custom', ms.is_custom, 'source_placeholder', ms.source_placeholder)) FILTER (WHERE (ms.workspace_id IS NOT NULL)), '[]'::json) AS mapping_settings_array,
    COALESCE(json_agg(json_build_object('cost_code_field_name', dfs.cost_code_field_name, 'cost_code_placeholder', dfs.cost_code_placeholder, 'cost_type_field_name', dfs.cost_type_field_name, 'cost_type_placeholder', dfs.cost_type_placeholder, 'is_import_enabled', dfs.is_import_enabled)) FILTER (WHERE (dfs.workspace_id IS NOT NULL)), '[]'::json) AS dependent_field_settings_array
   FROM ((((public.workspaces w
     JOIN public.configurations c ON ((w.id = c.workspace_id)))
     JOIN public.general_mappings gm ON ((w.id = gm.workspace_id)))
     LEFT JOIN public.mapping_settings ms ON ((w.id = ms.workspace_id)))
     LEFT JOIN public.dependent_field_settings dfs ON ((w.id = dfs.workspace_id)))
  GROUP BY w.id, w.name, w.fyle_org_id, c.import_categories, c.import_tax_codes, c.import_vendors_as_merchants, c.import_code_fields, gm.default_tax_code_name, gm.default_tax_code_id;


ALTER VIEW public.product_import_settings_view OWNER TO postgres;

--
-- Name: reimbursements; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reimbursements (
    id integer NOT NULL,
    settlement_id character varying(255) NOT NULL,
    reimbursement_id character varying(255) NOT NULL,
    state character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    payment_number character varying(255)
);


ALTER TABLE public.reimbursements OWNER TO postgres;

--
-- Name: reimbursements_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reimbursements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reimbursements_id_seq OWNER TO postgres;

--
-- Name: reimbursements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reimbursements_id_seq OWNED BY public.reimbursements.id;


--
-- Name: repetition_error_count_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.repetition_error_count_view AS
 SELECT count(*) AS count,
    current_database() AS database
   FROM public.errors
  WHERE ((errors.repetition_count > 20) AND (errors.workspace_id IN ( SELECT prod_workspaces_view.id
           FROM public.prod_workspaces_view)) AND (errors.is_resolved = false) AND (errors.created_at < (now() - '2 mons'::interval)));


ALTER VIEW public.repetition_error_count_view OWNER TO postgres;

--
-- Name: sage_intacct_attributes_count; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sage_intacct_attributes_count (
    id integer NOT NULL,
    accounts_count integer NOT NULL,
    items_count integer NOT NULL,
    vendors_count integer NOT NULL,
    employees_count integer NOT NULL,
    departments_count integer NOT NULL,
    classes_count integer NOT NULL,
    customers_count integer NOT NULL,
    projects_count integer NOT NULL,
    locations_count integer NOT NULL,
    expense_types_count integer NOT NULL,
    tax_details_count integer NOT NULL,
    cost_codes_count integer NOT NULL,
    cost_types_count integer NOT NULL,
    user_defined_dimensions_details jsonb,
    charge_card_accounts_count integer NOT NULL,
    payment_accounts_count integer NOT NULL,
    expense_payment_types_count integer NOT NULL,
    allocations_count integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL
);


ALTER TABLE public.sage_intacct_attributes_count OWNER TO postgres;

--
-- Name: sage_intacct_attributes_count_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.sage_intacct_attributes_count ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.sage_intacct_attributes_count_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: sage_intacct_bill_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_bill_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sage_intacct_bill_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_bill_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_bill_id_seq OWNED BY public.bills.id;


--
-- Name: sage_intacct_billlineitem_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_billlineitem_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sage_intacct_billlineitem_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_billlineitem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_billlineitem_id_seq OWNED BY public.bill_lineitems.id;


--
-- Name: sage_intacct_chargecardtransaction_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_chargecardtransaction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sage_intacct_chargecardtransaction_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_chargecardtransaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_chargecardtransaction_id_seq OWNED BY public.charge_card_transactions.id;


--
-- Name: sage_intacct_chargecardtransactionlineitem_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_chargecardtransactionlineitem_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sage_intacct_chargecardtransactionlineitem_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_chargecardtransactionlineitem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_chargecardtransactionlineitem_id_seq OWNED BY public.charge_card_transaction_lineitems.id;


--
-- Name: sage_intacct_credentials; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sage_intacct_credentials (
    id integer NOT NULL,
    si_user_id text NOT NULL,
    si_company_id text NOT NULL,
    si_company_name text,
    si_user_password text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    workspace_id integer NOT NULL,
    is_expired boolean NOT NULL,
    refresh_token text,
    access_token text,
    access_token_expires_at timestamp with time zone
);


ALTER TABLE public.sage_intacct_credentials OWNER TO postgres;

--
-- Name: sage_intacct_expensereport_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_expensereport_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sage_intacct_expensereport_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_expensereport_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_expensereport_id_seq OWNED BY public.expense_reports.id;


--
-- Name: sage_intacct_expensereportlineitem_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_expensereportlineitem_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sage_intacct_expensereportlineitem_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_expensereportlineitem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_expensereportlineitem_id_seq OWNED BY public.expense_report_lineitems.id;


--
-- Name: sage_intacct_reimbursement_lineitems; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sage_intacct_reimbursement_lineitems (
    id integer NOT NULL,
    amount double precision NOT NULL,
    record_key character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    sage_intacct_reimbursement_id integer NOT NULL
);


ALTER TABLE public.sage_intacct_reimbursement_lineitems OWNER TO postgres;

--
-- Name: sage_intacct_reimbursement_lineitems_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_reimbursement_lineitems_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sage_intacct_reimbursement_lineitems_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_reimbursement_lineitems_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_reimbursement_lineitems_id_seq OWNED BY public.sage_intacct_reimbursement_lineitems.id;


--
-- Name: sage_intacct_reimbursements; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sage_intacct_reimbursements (
    id integer NOT NULL,
    account_id character varying(255) NOT NULL,
    employee_id character varying(255) NOT NULL,
    memo text NOT NULL,
    payment_description text NOT NULL,
    created_at date NOT NULL,
    updated_at date NOT NULL,
    expense_group_id integer NOT NULL
);


ALTER TABLE public.sage_intacct_reimbursements OWNER TO postgres;

--
-- Name: sage_intacct_reimbursements_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sage_intacct_reimbursements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sage_intacct_reimbursements_id_seq OWNER TO postgres;

--
-- Name: sage_intacct_reimbursements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sage_intacct_reimbursements_id_seq OWNED BY public.sage_intacct_reimbursements.id;


--
-- Name: tasks_tasklog_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tasks_tasklog_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tasks_tasklog_id_seq OWNER TO postgres;

--
-- Name: tasks_tasklog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tasks_tasklog_id_seq OWNED BY public.task_logs.id;


--
-- Name: update_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.update_logs (
    id integer NOT NULL,
    table_name text,
    old_data jsonb,
    new_data jsonb,
    difference jsonb,
    workspace_id integer,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.update_logs OWNER TO postgres;

--
-- Name: update_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.update_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.update_logs_id_seq OWNER TO postgres;

--
-- Name: update_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.update_logs_id_seq OWNED BY public.update_logs.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    user_id character varying(255) NOT NULL,
    full_name character varying(255) NOT NULL,
    active boolean NOT NULL,
    staff boolean NOT NULL,
    admin boolean NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_user_id_seq OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.id;


--
-- Name: workspace_schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workspace_schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workspace_schedules_id_seq OWNER TO postgres;

--
-- Name: workspace_schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workspace_schedules_id_seq OWNED BY public.workspace_schedules.id;


--
-- Name: workspaces_fylecredential_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workspaces_fylecredential_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workspaces_fylecredential_id_seq OWNER TO postgres;

--
-- Name: workspaces_fylecredential_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workspaces_fylecredential_id_seq OWNED BY public.fyle_credentials.id;


--
-- Name: workspaces_sageintacctcredential_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workspaces_sageintacctcredential_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workspaces_sageintacctcredential_id_seq OWNER TO postgres;

--
-- Name: workspaces_sageintacctcredential_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workspaces_sageintacctcredential_id_seq OWNED BY public.sage_intacct_credentials.id;


--
-- Name: workspaces_user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workspaces_user (
    id integer NOT NULL,
    workspace_id integer NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.workspaces_user OWNER TO postgres;

--
-- Name: workspaces_workspace_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workspaces_workspace_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workspaces_workspace_id_seq OWNER TO postgres;

--
-- Name: workspaces_workspace_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workspaces_workspace_id_seq OWNED BY public.workspaces.id;


--
-- Name: workspaces_workspace_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workspaces_workspace_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workspaces_workspace_user_id_seq OWNER TO postgres;

--
-- Name: workspaces_workspace_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workspaces_workspace_user_id_seq OWNED BY public.workspaces_user.id;


--
-- Name: workspaces_workspacegeneralsettings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workspaces_workspacegeneralsettings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workspaces_workspacegeneralsettings_id_seq OWNER TO postgres;

--
-- Name: workspaces_workspacegeneralsettings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workspaces_workspacegeneralsettings_id_seq OWNED BY public.configurations.id;


--
-- Name: ap_payment_lineitems id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payment_lineitems ALTER COLUMN id SET DEFAULT nextval('public.ap_payment_lineitems_id_seq'::regclass);


--
-- Name: ap_payments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payments ALTER COLUMN id SET DEFAULT nextval('public.ap_payments_id_seq'::regclass);


--
-- Name: auth_group id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group ALTER COLUMN id SET DEFAULT nextval('public.auth_group_id_seq'::regclass);


--
-- Name: auth_group_permissions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions ALTER COLUMN id SET DEFAULT nextval('public.auth_group_permissions_id_seq'::regclass);


--
-- Name: auth_permission id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission ALTER COLUMN id SET DEFAULT nextval('public.auth_permission_id_seq'::regclass);


--
-- Name: auth_tokens id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_tokens ALTER COLUMN id SET DEFAULT nextval('public.fyle_rest_auth_authtokens_id_seq'::regclass);


--
-- Name: bill_lineitems id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bill_lineitems ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_billlineitem_id_seq'::regclass);


--
-- Name: bills id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bills ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_bill_id_seq'::regclass);


--
-- Name: category_mappings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_mappings ALTER COLUMN id SET DEFAULT nextval('public.category_mappings_id_seq'::regclass);


--
-- Name: charge_card_transaction_lineitems id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transaction_lineitems ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_chargecardtransactionlineitem_id_seq'::regclass);


--
-- Name: charge_card_transactions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transactions ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_chargecardtransaction_id_seq'::regclass);


--
-- Name: configurations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configurations ALTER COLUMN id SET DEFAULT nextval('public.workspaces_workspacegeneralsettings_id_seq'::regclass);


--
-- Name: cost_types id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cost_types ALTER COLUMN id SET DEFAULT nextval('public.cost_types_id_seq'::regclass);


--
-- Name: dependent_field_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dependent_field_settings ALTER COLUMN id SET DEFAULT nextval('public.dependent_fields_id_seq'::regclass);


--
-- Name: destination_attributes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_attributes ALTER COLUMN id SET DEFAULT nextval('public.fyle_accounting_mappings_destinationattribute_id_seq'::regclass);


--
-- Name: django_admin_log id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log ALTER COLUMN id SET DEFAULT nextval('public.django_admin_log_id_seq'::regclass);


--
-- Name: django_content_type id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type ALTER COLUMN id SET DEFAULT nextval('public.django_content_type_id_seq'::regclass);


--
-- Name: django_migrations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_migrations ALTER COLUMN id SET DEFAULT nextval('public.django_migrations_id_seq'::regclass);


--
-- Name: django_q_ormq id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_q_ormq ALTER COLUMN id SET DEFAULT nextval('public.django_q_ormq_id_seq'::regclass);


--
-- Name: django_q_schedule id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_q_schedule ALTER COLUMN id SET DEFAULT nextval('public.django_q_schedule_id_seq'::regclass);


--
-- Name: employee_mappings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings ALTER COLUMN id SET DEFAULT nextval('public.employee_mappings_id_seq'::regclass);


--
-- Name: errors id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.errors ALTER COLUMN id SET DEFAULT nextval('public.errors_id_seq'::regclass);


--
-- Name: expense_attributes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_attributes ALTER COLUMN id SET DEFAULT nextval('public.fyle_accounting_mappings_expenseattribute_id_seq'::regclass);


--
-- Name: expense_attributes_deletion_cache id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_attributes_deletion_cache ALTER COLUMN id SET DEFAULT nextval('public.expense_attributes_deletion_cache_id_seq'::regclass);


--
-- Name: expense_fields id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_fields ALTER COLUMN id SET DEFAULT nextval('public.expense_fields_id_seq'::regclass);


--
-- Name: expense_filters id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_filters ALTER COLUMN id SET DEFAULT nextval('public.expense_filters_id_seq'::regclass);


--
-- Name: expense_group_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_group_settings ALTER COLUMN id SET DEFAULT nextval('public.expense_group_settings_id_seq'::regclass);


--
-- Name: expense_groups id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups ALTER COLUMN id SET DEFAULT nextval('public.fyle_expensegroup_id_seq'::regclass);


--
-- Name: expense_groups_expenses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups_expenses ALTER COLUMN id SET DEFAULT nextval('public.fyle_expensegroup_expenses_id_seq'::regclass);


--
-- Name: expense_report_lineitems id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_report_lineitems ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_expensereportlineitem_id_seq'::regclass);


--
-- Name: expense_reports id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_reports ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_expensereport_id_seq'::regclass);


--
-- Name: expenses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses ALTER COLUMN id SET DEFAULT nextval('public.fyle_expense_id_seq'::regclass);


--
-- Name: fyle_credentials id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fyle_credentials ALTER COLUMN id SET DEFAULT nextval('public.workspaces_fylecredential_id_seq'::regclass);


--
-- Name: general_mappings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.general_mappings ALTER COLUMN id SET DEFAULT nextval('public.mappings_generalmapping_id_seq'::regclass);


--
-- Name: import_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.import_logs ALTER COLUMN id SET DEFAULT nextval('public.import_logs_id_seq'::regclass);


--
-- Name: journal_entries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entries ALTER COLUMN id SET DEFAULT nextval('public.journal_entries_id_seq'::regclass);


--
-- Name: journal_entry_lineitems id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entry_lineitems ALTER COLUMN id SET DEFAULT nextval('public.journal_entry_lineitems_id_seq'::regclass);


--
-- Name: last_export_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.last_export_details ALTER COLUMN id SET DEFAULT nextval('public.last_export_details_id_seq'::regclass);


--
-- Name: location_entity_mappings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.location_entity_mappings ALTER COLUMN id SET DEFAULT nextval('public.location_entity_mappings_id_seq'::regclass);


--
-- Name: mapping_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mapping_settings ALTER COLUMN id SET DEFAULT nextval('public.fyle_accounting_mappings_mappingsetting_id_seq'::regclass);


--
-- Name: mappings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mappings ALTER COLUMN id SET DEFAULT nextval('public.fyle_accounting_mappings_mapping_id_seq'::regclass);


--
-- Name: reimbursements id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reimbursements ALTER COLUMN id SET DEFAULT nextval('public.reimbursements_id_seq'::regclass);


--
-- Name: sage_intacct_credentials id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_credentials ALTER COLUMN id SET DEFAULT nextval('public.workspaces_sageintacctcredential_id_seq'::regclass);


--
-- Name: sage_intacct_reimbursement_lineitems id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursement_lineitems ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_reimbursement_lineitems_id_seq'::regclass);


--
-- Name: sage_intacct_reimbursements id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursements ALTER COLUMN id SET DEFAULT nextval('public.sage_intacct_reimbursements_id_seq'::regclass);


--
-- Name: task_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs ALTER COLUMN id SET DEFAULT nextval('public.tasks_tasklog_id_seq'::regclass);


--
-- Name: update_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.update_logs ALTER COLUMN id SET DEFAULT nextval('public.update_logs_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Name: workspace_schedules id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspace_schedules ALTER COLUMN id SET DEFAULT nextval('public.workspace_schedules_id_seq'::regclass);


--
-- Name: workspaces id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces ALTER COLUMN id SET DEFAULT nextval('public.workspaces_workspace_id_seq'::regclass);


--
-- Name: workspaces_user id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces_user ALTER COLUMN id SET DEFAULT nextval('public.workspaces_workspace_user_id_seq'::regclass);


--
-- Data for Name: ap_payment_lineitems; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ap_payment_lineitems (id, amount, record_key, created_at, updated_at, ap_payment_id) FROM stdin;
\.


--
-- Data for Name: ap_payments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ap_payments (id, payment_account_id, vendor_id, description, currency, created_at, updated_at, expense_group_id) FROM stdin;
\.


--
-- Data for Name: auth_cache; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_cache (cache_key, value, expires) FROM stdin;
\.


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add content type	4	add_contenttype
14	Can change content type	4	change_contenttype
15	Can delete content type	4	delete_contenttype
16	Can view content type	4	view_contenttype
17	Can add session	5	add_session
18	Can change session	5	change_session
19	Can delete session	5	delete_session
20	Can view session	5	view_session
21	Can add Scheduled task	6	add_schedule
22	Can change Scheduled task	6	change_schedule
23	Can delete Scheduled task	6	delete_schedule
24	Can view Scheduled task	6	view_schedule
25	Can add task	7	add_task
26	Can change task	7	change_task
27	Can delete task	7	delete_task
28	Can view task	7	view_task
29	Can add Failed task	8	add_failure
30	Can change Failed task	8	change_failure
31	Can delete Failed task	8	delete_failure
32	Can view Failed task	8	view_failure
33	Can add Successful task	9	add_success
34	Can change Successful task	9	change_success
35	Can delete Successful task	9	delete_success
36	Can view Successful task	9	view_success
37	Can add Queued task	10	add_ormq
38	Can change Queued task	10	change_ormq
39	Can delete Queued task	10	delete_ormq
40	Can view Queued task	10	view_ormq
41	Can add auth token	11	add_authtoken
42	Can change auth token	11	change_authtoken
43	Can delete auth token	11	delete_authtoken
44	Can view auth token	11	view_authtoken
45	Can add destination attribute	12	add_destinationattribute
46	Can change destination attribute	12	change_destinationattribute
47	Can delete destination attribute	12	delete_destinationattribute
48	Can view destination attribute	12	view_destinationattribute
49	Can add expense attribute	13	add_expenseattribute
50	Can change expense attribute	13	change_expenseattribute
51	Can delete expense attribute	13	delete_expenseattribute
52	Can view expense attribute	13	view_expenseattribute
53	Can add mapping setting	14	add_mappingsetting
54	Can change mapping setting	14	change_mappingsetting
55	Can delete mapping setting	14	delete_mappingsetting
56	Can view mapping setting	14	view_mappingsetting
57	Can add mapping	15	add_mapping
58	Can change mapping	15	change_mapping
59	Can delete mapping	15	delete_mapping
60	Can view mapping	15	view_mapping
61	Can add employee mapping	16	add_employeemapping
62	Can change employee mapping	16	change_employeemapping
63	Can delete employee mapping	16	delete_employeemapping
64	Can view employee mapping	16	view_employeemapping
65	Can add category mapping	17	add_categorymapping
66	Can change category mapping	17	change_categorymapping
67	Can delete category mapping	17	delete_categorymapping
68	Can view category mapping	17	view_categorymapping
69	Can add user	18	add_user
70	Can change user	18	change_user
71	Can delete user	18	delete_user
72	Can view user	18	view_user
73	Can add workspace	19	add_workspace
74	Can change workspace	19	change_workspace
75	Can delete workspace	19	delete_workspace
76	Can view workspace	19	view_workspace
77	Can add sage intacct credential	20	add_sageintacctcredential
78	Can change sage intacct credential	20	change_sageintacctcredential
79	Can delete sage intacct credential	20	delete_sageintacctcredential
80	Can view sage intacct credential	20	view_sageintacctcredential
81	Can add fyle credential	21	add_fylecredential
82	Can change fyle credential	21	change_fylecredential
83	Can delete fyle credential	21	delete_fylecredential
84	Can view fyle credential	21	view_fylecredential
85	Can add workspace schedule	22	add_workspaceschedule
86	Can change workspace schedule	22	change_workspaceschedule
87	Can delete workspace schedule	22	delete_workspaceschedule
88	Can view workspace schedule	22	view_workspaceschedule
89	Can add configuration	23	add_configuration
90	Can change configuration	23	change_configuration
91	Can delete configuration	23	delete_configuration
92	Can view configuration	23	view_configuration
93	Can add expense	24	add_expense
94	Can change expense	24	change_expense
95	Can delete expense	24	delete_expense
96	Can view expense	24	view_expense
97	Can add expense group	25	add_expensegroup
98	Can change expense group	25	change_expensegroup
99	Can delete expense group	25	delete_expensegroup
100	Can view expense group	25	view_expensegroup
101	Can add expense group settings	26	add_expensegroupsettings
102	Can change expense group settings	26	change_expensegroupsettings
103	Can delete expense group settings	26	delete_expensegroupsettings
104	Can view expense group settings	26	view_expensegroupsettings
105	Can add reimbursement	27	add_reimbursement
106	Can change reimbursement	27	change_reimbursement
107	Can delete reimbursement	27	delete_reimbursement
108	Can view reimbursement	27	view_reimbursement
109	Can add bill	28	add_bill
110	Can change bill	28	change_bill
111	Can delete bill	28	delete_bill
112	Can view bill	28	view_bill
113	Can add bill lineitem	29	add_billlineitem
114	Can change bill lineitem	29	change_billlineitem
115	Can delete bill lineitem	29	delete_billlineitem
116	Can view bill lineitem	29	view_billlineitem
117	Can add expense report	30	add_expensereport
118	Can change expense report	30	change_expensereport
119	Can delete expense report	30	delete_expensereport
120	Can view expense report	30	view_expensereport
121	Can add expense report lineitem	31	add_expensereportlineitem
122	Can change expense report lineitem	31	change_expensereportlineitem
123	Can delete expense report lineitem	31	delete_expensereportlineitem
124	Can view expense report lineitem	31	view_expensereportlineitem
125	Can add charge card transaction	32	add_chargecardtransaction
126	Can change charge card transaction	32	change_chargecardtransaction
127	Can delete charge card transaction	32	delete_chargecardtransaction
128	Can view charge card transaction	32	view_chargecardtransaction
129	Can add charge card transaction lineitem	33	add_chargecardtransactionlineitem
130	Can change charge card transaction lineitem	33	change_chargecardtransactionlineitem
131	Can delete charge card transaction lineitem	33	delete_chargecardtransactionlineitem
132	Can view charge card transaction lineitem	33	view_chargecardtransactionlineitem
133	Can add ap payment	34	add_appayment
134	Can change ap payment	34	change_appayment
135	Can delete ap payment	34	delete_appayment
136	Can view ap payment	34	view_appayment
137	Can add sage intacct reimbursement	35	add_sageintacctreimbursement
138	Can change sage intacct reimbursement	35	change_sageintacctreimbursement
139	Can delete sage intacct reimbursement	35	delete_sageintacctreimbursement
140	Can view sage intacct reimbursement	35	view_sageintacctreimbursement
141	Can add sage intacct reimbursement lineitem	36	add_sageintacctreimbursementlineitem
142	Can change sage intacct reimbursement lineitem	36	change_sageintacctreimbursementlineitem
143	Can delete sage intacct reimbursement lineitem	36	delete_sageintacctreimbursementlineitem
144	Can view sage intacct reimbursement lineitem	36	view_sageintacctreimbursementlineitem
145	Can add ap payment lineitem	37	add_appaymentlineitem
146	Can change ap payment lineitem	37	change_appaymentlineitem
147	Can delete ap payment lineitem	37	delete_appaymentlineitem
148	Can view ap payment lineitem	37	view_appaymentlineitem
149	Can add journal entry	38	add_journalentry
150	Can change journal entry	38	change_journalentry
151	Can delete journal entry	38	delete_journalentry
152	Can view journal entry	38	view_journalentry
153	Can add journal entry lineitem	39	add_journalentrylineitem
154	Can change journal entry lineitem	39	change_journalentrylineitem
155	Can delete journal entry lineitem	39	delete_journalentrylineitem
156	Can view journal entry lineitem	39	view_journalentrylineitem
157	Can add task log	40	add_tasklog
158	Can change task log	40	change_tasklog
159	Can delete task log	40	delete_tasklog
160	Can view task log	40	view_tasklog
161	Can add general mapping	41	add_generalmapping
162	Can change general mapping	41	change_generalmapping
163	Can delete general mapping	41	delete_generalmapping
164	Can view general mapping	41	view_generalmapping
165	Can add location entity mapping	42	add_locationentitymapping
166	Can change location entity mapping	42	change_locationentitymapping
167	Can delete location entity mapping	42	delete_locationentitymapping
168	Can view location entity mapping	42	view_locationentitymapping
169	Can add expense field	43	add_expensefield
170	Can change expense field	43	change_expensefield
171	Can delete expense field	43	delete_expensefield
172	Can view expense field	43	view_expensefield
173	Can add expense filter	44	add_expensefilter
174	Can change expense filter	44	change_expensefilter
175	Can delete expense filter	44	delete_expensefilter
176	Can view expense filter	44	view_expensefilter
177	Can add dependent field setting	45	add_dependentfieldsetting
178	Can change dependent field setting	45	change_dependentfieldsetting
179	Can delete dependent field setting	45	delete_dependentfieldsetting
180	Can view dependent field setting	45	view_dependentfieldsetting
181	Can add cost type	46	add_costtype
182	Can change cost type	46	change_costtype
183	Can delete cost type	46	delete_costtype
184	Can view cost type	46	view_costtype
185	Can add error	47	add_error
186	Can change error	47	change_error
187	Can delete error	47	delete_error
188	Can view error	47	view_error
189	Can add last export detail	48	add_lastexportdetail
190	Can change last export detail	48	change_lastexportdetail
191	Can delete last export detail	48	delete_lastexportdetail
192	Can view last export detail	48	view_lastexportdetail
193	Can add import log	49	add_importlog
194	Can change import log	49	change_importlog
195	Can delete import log	49	delete_importlog
196	Can view import log	49	view_importlog
197	Can add expense attributes deletion cache	50	add_expenseattributesdeletioncache
198	Can change expense attributes deletion cache	50	change_expenseattributesdeletioncache
199	Can delete expense attributes deletion cache	50	delete_expenseattributesdeletioncache
200	Can view expense attributes deletion cache	50	view_expenseattributesdeletioncache
201	Can add dimension detail	51	add_dimensiondetail
202	Can change dimension detail	51	change_dimensiondetail
203	Can delete dimension detail	51	delete_dimensiondetail
204	Can view dimension detail	51	view_dimensiondetail
205	Can add failed event	52	add_failedevent
206	Can change failed event	52	change_failedevent
207	Can delete failed event	52	delete_failedevent
208	Can view failed event	52	view_failedevent
209	Can add cost code	53	add_costcode
210	Can change cost code	53	change_costcode
211	Can delete cost code	53	delete_costcode
212	Can view cost code	53	view_costcode
213	Can add feature config	54	add_featureconfig
214	Can change feature config	54	change_featureconfig
215	Can delete feature config	54	delete_featureconfig
216	Can view feature config	54	view_featureconfig
217	Can add fyle sync timestamp	55	add_fylesynctimestamp
218	Can change fyle sync timestamp	55	change_fylesynctimestamp
219	Can delete fyle sync timestamp	55	delete_fylesynctimestamp
220	Can view fyle sync timestamp	55	view_fylesynctimestamp
221	Can add intacct synced timestamp	56	add_intacctsyncedtimestamp
222	Can change intacct synced timestamp	56	change_intacctsyncedtimestamp
223	Can delete intacct synced timestamp	56	delete_intacctsyncedtimestamp
224	Can view intacct synced timestamp	56	view_intacctsyncedtimestamp
225	Can add sage intacct attributes count	57	add_sageintacctattributescount
226	Can change sage intacct attributes count	57	change_sageintacctattributescount
227	Can delete sage intacct attributes count	57	delete_sageintacctattributescount
228	Can view sage intacct attributes count	57	view_sageintacctattributescount
\.


--
-- Data for Name: auth_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_tokens (id, refresh_token, user_id) FROM stdin;
1	eyJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NjM2NjMwNzIsImlzcyI6IkZ5bGVBcHAiLCJvcmdfdXNlcl9pZCI6Ilwib3VWTE9ZUDhsZWxOXCIiLCJ0cGFfaWQiOiJcInRwYXlmalBQSFREZ3ZcIiIsInRwYV9uYW1lIjoiXCJGeWxlIDw-IFNhZ2UgSW4uLlwiIiwiY2x1c3Rlcl9kb21haW4iOiJcImh0dHBzOi8vc3RhZ2luZy5meWxlLnRlY2hcIiIsImV4cCI6MTk3OTAyMzA3Mn0.NGRySUzDx7ycSD_6LaRy_wTGMD7Yl-u3I1FmOo9BWhk	1
\.


--
-- Data for Name: bill_lineitems; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bill_lineitems (id, expense_type_id, gl_account_number, project_id, location_id, department_id, memo, amount, created_at, updated_at, bill_id, expense_id, billable, customer_id, item_id, user_defined_dimensions, class_id, tax_amount, tax_code, cost_type_id, task_id, allocation_id) FROM stdin;
\.


--
-- Data for Name: bills; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bills (id, vendor_id, description, supdoc_id, created_at, updated_at, expense_group_id, memo, transaction_date, paid_on_sage_intacct, payment_synced, currency, is_retired) FROM stdin;
\.


--
-- Data for Name: category_mappings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.category_mappings (id, created_at, updated_at, destination_account_id, destination_expense_head_id, source_category_id, workspace_id) FROM stdin;
1	2022-09-20 08:40:38.707759+00	2022-09-20 08:40:38.70782+00	792	927	26	1
2	2022-09-20 08:40:38.707876+00	2022-09-20 08:40:38.707906+00	792	931	20	1
3	2022-09-20 08:40:38.707955+00	2022-09-20 08:40:38.707984+00	792	928	27	1
4	2022-09-20 08:40:38.708033+00	2022-09-20 08:40:38.708062+00	807	930	23	1
5	2022-09-20 08:40:38.708112+00	2022-09-20 08:40:38.708149+00	807	932	21	1
6	2022-09-20 08:40:38.70843+00	2022-09-20 08:40:38.708473+00	796	929	22	1
7	2022-09-20 08:40:38.708547+00	2022-09-20 08:40:38.708578+00	796	926	25	1
8	2022-09-20 08:40:38.70874+00	2022-09-20 08:40:38.708764+00	792	925	24	1
9	2022-09-20 08:49:07.95636+00	2022-09-20 08:49:07.956416+00	896	\N	325	1
10	2022-09-28 11:56:20.729414+00	2022-09-28 11:56:20.729471+00	756	\N	327	1
\.


--
-- Data for Name: charge_card_transaction_lineitems; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.charge_card_transaction_lineitems (id, gl_account_number, project_id, location_id, department_id, amount, created_at, updated_at, charge_card_transaction_id, expense_id, memo, customer_id, item_id, class_id, tax_amount, tax_code, cost_type_id, task_id, user_defined_dimensions, billable, vendor_id) FROM stdin;
\.


--
-- Data for Name: charge_card_transactions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.charge_card_transactions (id, charge_card_id, description, supdoc_id, created_at, updated_at, expense_group_id, memo, transaction_date, currency, reference_no, vendor_id, payee) FROM stdin;
\.


--
-- Data for Name: configurations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.configurations (id, reimbursable_expenses_object, created_at, updated_at, workspace_id, corporate_credit_card_expenses_object, import_projects, sync_fyle_to_sage_intacct_payments, sync_sage_intacct_to_fyle_payments, auto_map_employees, import_categories, auto_create_destination_entity, memo_structure, import_tax_codes, change_accounting_period, import_vendors_as_merchants, employee_field_mapping, use_merchant_in_journal_line, is_journal_credit_billable, auto_create_merchants_as_vendors, import_code_fields, created_by, updated_by, skip_accounting_export_summary_post, je_single_credit_line, top_level_memo_structure) FROM stdin;
1	BILL	2022-09-20 08:39:32.015647+00	2022-09-20 08:46:24.926422+00	1	BILL	t	t	f	EMAIL	f	t	{employee_email,category,spent_on,report_number,purpose,expense_link}	t	t	t	VENDOR	f	t	f	{}	\N	\N	f	f	{}
\.


--
-- Data for Name: cost_codes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cost_codes (id, task_id, task_name, project_id, project_name, created_at, updated_at, workspace_id) FROM stdin;
\.


--
-- Data for Name: cost_types; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cost_types (id, record_number, project_key, project_id, project_name, task_key, task_id, status, task_name, cost_type_id, name, when_created, when_modified, created_at, updated_at, workspace_id, is_imported) FROM stdin;
\.


--
-- Data for Name: dependent_field_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.dependent_field_settings (id, is_import_enabled, project_field_id, cost_code_field_name, cost_code_field_id, cost_type_field_name, cost_type_field_id, last_successful_import_at, created_at, updated_at, workspace_id, cost_code_placeholder, cost_type_placeholder, last_synced_at, is_cost_type_import_enabled) FROM stdin;
\.


--
-- Data for Name: destination_attributes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.destination_attributes (id, attribute_type, display_name, value, destination_id, created_at, updated_at, workspace_id, active, detail, auto_created, code) FROM stdin;
1	LOCATION_ENTITY	location entity	USA 1	100	2022-09-20 08:38:53.467623+00	2022-09-20 08:38:53.467654+00	1	\N	{"country": "United States"}	f	\N
2	LOCATION_ENTITY	location entity	USA 2	200	2022-09-20 08:38:53.467725+00	2022-09-20 08:38:53.467767+00	1	\N	{"country": "United States"}	f	\N
3	LOCATION_ENTITY	location entity	Holding Company	300	2022-09-20 08:38:53.467858+00	2022-09-20 08:38:53.467892+00	1	\N	{"country": "United States"}	f	\N
4	LOCATION_ENTITY	location entity	Canada	400	2022-09-20 08:38:53.467952+00	2022-09-20 08:38:53.467974+00	1	\N	{"country": "Canada"}	f	\N
5	LOCATION_ENTITY	location entity	United Kingdom	500	2022-09-20 08:38:53.468564+00	2022-09-20 08:38:53.468612+00	1	\N	{"country": "United Kingdom"}	f	\N
6	LOCATION_ENTITY	location entity	Australia	600	2022-09-20 08:38:53.468695+00	2022-09-20 08:38:53.468719+00	1	\N	{"country": "Australia"}	f	\N
7	LOCATION_ENTITY	location entity	South Africa	700	2022-09-20 08:38:53.468885+00	2022-09-20 08:38:53.468927+00	1	\N	{"country": "South Africa"}	f	\N
8	LOCATION_ENTITY	location entity	Elimination - NA	900	2022-09-20 08:38:53.469363+00	2022-09-20 08:38:53.469389+00	1	\N	{"country": null}	f	\N
9	LOCATION_ENTITY	location entity	Elimination - Global	910	2022-09-20 08:38:53.469468+00	2022-09-20 08:38:53.469498+00	1	\N	{"country": null}	f	\N
10	LOCATION_ENTITY	location entity	Elimination - Sub	920	2022-09-20 08:38:53.46957+00	2022-09-20 08:38:53.46959+00	1	\N	{"country": null}	f	\N
11	LOCATION	location	Australia	600	2022-09-20 08:39:08.709874+00	2022-09-20 08:39:08.709918+00	1	\N	\N	f	\N
12	LOCATION	location	New South Wales	700-New South Wales	2022-09-20 08:39:08.709971+00	2022-09-20 08:39:08.709999+00	1	\N	\N	f	\N
13	CUSTOMER	customer	AB SQUARE	10001	2022-09-20 08:39:16.581594+00	2022-09-20 08:39:16.581644+00	1	\N	\N	f	\N
14	CUSTOMER	customer	EZ Services	10002	2022-09-20 08:39:16.581716+00	2022-09-20 08:39:16.581749+00	1	\N	\N	f	\N
15	CUSTOMER	customer	Uplift Services	10003	2022-09-20 08:39:16.581815+00	2022-09-20 08:39:16.581847+00	1	\N	\N	f	\N
16	CUSTOMER	customer	Sagacent Finance	10004	2022-09-20 08:39:16.581966+00	2022-09-20 08:39:16.582022+00	1	\N	\N	f	\N
17	CUSTOMER	customer	Nirvana	10005	2022-09-20 08:39:16.582145+00	2022-09-20 08:39:16.582199+00	1	\N	\N	f	\N
18	CUSTOMER	customer	AG Insurance	10006	2022-09-20 08:39:16.582471+00	2022-09-20 08:39:16.58252+00	1	\N	\N	f	\N
19	CUSTOMER	customer	RedFin Insurance	10007	2022-09-20 08:39:16.582626+00	2022-09-20 08:39:16.582657+00	1	\N	\N	f	\N
20	CUSTOMER	customer	Cvibe Insurance	10008	2022-09-20 08:39:16.582715+00	2022-09-20 08:39:16.582745+00	1	\N	\N	f	\N
21	CUSTOMER	customer	CostLess Insurance	10009	2022-09-20 08:39:16.582802+00	2022-09-20 08:39:16.582831+00	1	\N	\N	f	\N
22	CUSTOMER	customer	Community Agency Services	10010	2022-09-20 08:39:16.582888+00	2022-09-20 08:39:16.582918+00	1	\N	\N	f	\N
23	CUSTOMER	customer	GBD Inc	10011	2022-09-20 08:39:16.582975+00	2022-09-20 08:39:16.583004+00	1	\N	\N	f	\N
24	CUSTOMER	customer	MK Manufacturing	10012	2022-09-20 08:39:16.583061+00	2022-09-20 08:39:16.5831+00	1	\N	\N	f	\N
25	CUSTOMER	customer	Gemini Manufacturing Services	10013	2022-09-20 08:39:16.583168+00	2022-09-20 08:39:16.583197+00	1	\N	\N	f	\N
26	CUSTOMER	customer	Fab Seven	10014	2022-09-20 08:39:16.583263+00	2022-09-20 08:39:16.583302+00	1	\N	\N	f	\N
27	CUSTOMER	customer	GS Industries	10015	2022-09-20 08:39:16.583537+00	2022-09-20 08:39:16.583577+00	1	\N	\N	f	\N
28	CUSTOMER	customer	BioClear	10016	2022-09-20 08:39:16.583663+00	2022-09-20 08:39:16.583693+00	1	\N	\N	f	\N
29	CUSTOMER	customer	Applied Biomics	10017	2022-09-20 08:39:16.583752+00	2022-09-20 08:39:16.583781+00	1	\N	\N	f	\N
30	CUSTOMER	customer	Proton Centric	10018	2022-09-20 08:39:16.583839+00	2022-09-20 08:39:16.583868+00	1	\N	\N	f	\N
31	CUSTOMER	customer	BioMed Labs	10019	2022-09-20 08:39:16.583925+00	2022-09-20 08:39:16.583956+00	1	\N	\N	f	\N
32	CUSTOMER	customer	Nanocell	10020	2022-09-20 08:39:16.584035+00	2022-09-20 08:39:16.584066+00	1	\N	\N	f	\N
33	CUSTOMER	customer	Genentech, Inc.	10021	2022-09-20 08:39:16.584123+00	2022-09-20 08:39:16.584153+00	1	\N	\N	f	\N
34	CUSTOMER	customer	Matrox Electronic Systems Ltd.	10022	2022-09-20 08:39:16.58421+00	2022-09-20 08:39:16.584239+00	1	\N	\N	f	\N
35	CUSTOMER	customer	Pacificorp	10023	2022-09-20 08:39:16.58442+00	2022-09-20 08:39:16.584461+00	1	\N	\N	f	\N
36	CUSTOMER	customer	Virtela Communications	10024	2022-09-20 08:39:16.584515+00	2022-09-20 08:39:16.584543+00	1	\N	\N	f	\N
37	CUSTOMER	customer	Sonicwall, Inc.	10025	2022-09-20 08:39:16.584607+00	2022-09-20 08:39:16.584845+00	1	\N	\N	f	\N
38	CUSTOMER	customer	Spencer, Scott and Dwyer	10026	2022-09-20 08:39:16.584926+00	2022-09-20 08:39:16.584955+00	1	\N	\N	f	\N
39	CUSTOMER	customer	Klondike Gold Corporation	10027	2022-09-20 08:39:16.585011+00	2022-09-20 08:39:16.585038+00	1	\N	\N	f	\N
40	CUSTOMER	customer	Davis and Young LPA	10028	2022-09-20 08:39:16.585092+00	2022-09-20 08:39:16.585235+00	1	\N	\N	f	\N
41	CUSTOMER	customer	Bayer Corporation	10029	2022-09-20 08:39:16.585328+00	2022-09-20 08:39:16.585376+00	1	\N	\N	f	\N
42	CUSTOMER	customer	Rand Corporation	10030	2022-09-20 08:39:16.5855+00	2022-09-20 08:39:16.585671+00	1	\N	\N	f	\N
43	CUSTOMER	customer	Cleco Corporation	10031	2022-09-20 08:39:16.585737+00	2022-09-20 08:39:16.585766+00	1	\N	\N	f	\N
44	CUSTOMER	customer	Leo A. Daly Company	10032	2022-09-20 08:39:16.585986+00	2022-09-20 08:39:16.586041+00	1	\N	\N	f	\N
45	CUSTOMER	customer	United Security Bank	10033	2022-09-20 08:39:16.586148+00	2022-09-20 08:39:16.586191+00	1	\N	\N	f	\N
46	CUSTOMER	customer	Novamed	10034	2022-09-20 08:39:16.586298+00	2022-09-20 08:39:16.586346+00	1	\N	\N	f	\N
47	CUSTOMER	customer	Render	10041	2022-09-20 08:39:16.586447+00	2022-09-20 08:39:16.586611+00	1	\N	\N	f	\N
48	CUSTOMER	customer	Projo	10042	2022-09-20 08:39:16.586725+00	2022-09-20 08:39:16.58679+00	1	\N	\N	f	\N
49	CUSTOMER	customer	Finscent	10043	2022-09-20 08:39:16.587077+00	2022-09-20 08:39:16.587276+00	1	\N	\N	f	\N
50	CUSTOMER	customer	Innovation Arch	10044	2022-09-20 08:39:16.587528+00	2022-09-20 08:39:16.587573+00	1	\N	\N	f	\N
51	CUSTOMER	customer	Admire Arts	10051	2022-09-20 08:39:16.587676+00	2022-09-20 08:39:16.587715+00	1	\N	\N	f	\N
52	CUSTOMER	customer	Candor Corp	10052	2022-09-20 08:39:16.587949+00	2022-09-20 08:39:16.588073+00	1	\N	\N	f	\N
53	CUSTOMER	customer	Clerby	10053	2022-09-20 08:39:16.588218+00	2022-09-20 08:39:16.588306+00	1	\N	\N	f	\N
54	CUSTOMER	customer	Neoveo	10054	2022-09-20 08:39:16.58861+00	2022-09-20 08:39:16.588641+00	1	\N	\N	f	\N
55	CUSTOMER	customer	Avu	10061	2022-09-20 08:39:16.588699+00	2022-09-20 08:39:16.588726+00	1	\N	\N	f	\N
56	CUSTOMER	customer	Vertous	10062	2022-09-20 08:39:16.58878+00	2022-09-20 08:39:16.588818+00	1	\N	\N	f	\N
57	CUSTOMER	customer	Portore	10063	2022-09-20 08:39:16.588884+00	2022-09-20 08:39:16.588912+00	1	\N	\N	f	\N
58	CUSTOMER	customer	Med dot	10064	2022-09-20 08:39:16.588965+00	2022-09-20 08:39:16.588992+00	1	\N	\N	f	\N
59	CUSTOMER	customer	Proweb	10071	2022-09-20 08:39:16.589045+00	2022-09-20 08:39:16.589072+00	1	\N	\N	f	\N
60	CUSTOMER	customer	Focus Med	10072	2022-09-20 08:39:16.589127+00	2022-09-20 08:39:16.589154+00	1	\N	\N	f	\N
61	CUSTOMER	customer	Global Manufacturing	10073	2022-09-20 08:39:16.589206+00	2022-09-20 08:39:16.589234+00	1	\N	\N	f	\N
62	CUSTOMER	customer	Digital Bio	10074	2022-09-20 08:39:16.589287+00	2022-09-20 08:39:16.589313+00	1	\N	\N	f	\N
63	CUSTOMER	customer	new customer	10075	2022-09-20 08:39:16.595177+00	2022-09-20 08:39:16.595221+00	1	\N	\N	f	\N
64	CUSTOMER	customer	Entity 100	10100	2022-09-20 08:39:16.595287+00	2022-09-20 08:39:16.595464+00	1	\N	\N	f	\N
65	CUSTOMER	customer	Entity 200	10200	2022-09-20 08:39:16.595539+00	2022-09-20 08:39:16.595568+00	1	\N	\N	f	\N
66	CUSTOMER	customer	Entity 300	10300	2022-09-20 08:39:16.595624+00	2022-09-20 08:39:16.595652+00	1	\N	\N	f	\N
67	CUSTOMER	customer	Entity 400	10400	2022-09-20 08:39:16.595707+00	2022-09-20 08:39:16.595736+00	1	\N	\N	f	\N
68	CUSTOMER	customer	Entity 500	10500	2022-09-20 08:39:16.595791+00	2022-09-20 08:39:16.595818+00	1	\N	\N	f	\N
69	CUSTOMER	customer	Entity 600	10600	2022-09-20 08:39:16.595872+00	2022-09-20 08:39:16.5959+00	1	\N	\N	f	\N
70	CUSTOMER	customer	Entity 700	10700	2022-09-20 08:39:16.595955+00	2022-09-20 08:39:16.595982+00	1	\N	\N	f	\N
71	CUSTOMER	customer	Corley Energy	11001	2022-09-20 08:39:16.596036+00	2022-09-20 08:39:16.596064+00	1	\N	\N	f	\N
72	CUSTOMER	customer	National Clean Energy	11002	2022-09-20 08:39:16.596117+00	2022-09-20 08:39:16.596145+00	1	\N	\N	f	\N
73	CUSTOMER	customer	Porter Technologies	11003	2022-09-20 08:39:16.596199+00	2022-09-20 08:39:16.596227+00	1	\N	\N	f	\N
74	CUSTOMER	customer	Powell Clean Tech	11004	2022-09-20 08:39:16.59628+00	2022-09-20 08:39:16.596308+00	1	\N	\N	f	\N
75	CUSTOMER	customer	Vaillante	11005	2022-09-20 08:39:16.596372+00	2022-09-20 08:39:16.596512+00	1	\N	\N	f	\N
76	CUSTOMER	customer	Vapid Battery	11006	2022-09-20 08:39:16.596578+00	2022-09-20 08:39:16.596606+00	1	\N	\N	f	\N
77	CUSTOMER	customer	Acme	11007	2022-09-20 08:39:16.59666+00	2022-09-20 08:39:16.596687+00	1	\N	\N	f	\N
78	CUSTOMER	customer	ARCAM Corporation	11008	2022-09-20 08:39:16.596741+00	2022-09-20 08:39:16.596768+00	1	\N	\N	f	\N
79	CUSTOMER	customer	Biffco	11009	2022-09-20 08:39:16.596821+00	2022-09-20 08:39:16.596849+00	1	\N	\N	f	\N
80	CUSTOMER	customer	Binford	11010	2022-09-20 08:39:16.596902+00	2022-09-20 08:39:16.596929+00	1	\N	\N	f	\N
81	CUSTOMER	customer	Blue Sun Corporation	11011	2022-09-20 08:39:16.596982+00	2022-09-20 08:39:16.59701+00	1	\N	\N	f	\N
82	CUSTOMER	customer	Buynlarge Corporation	11012	2022-09-20 08:39:16.597063+00	2022-09-20 08:39:16.59709+00	1	\N	\N	f	\N
83	CUSTOMER	customer	Gadgetron	11013	2022-09-20 08:39:16.597143+00	2022-09-20 08:39:16.597182+00	1	\N	\N	f	\N
84	CUSTOMER	customer	Itex	11014	2022-09-20 08:39:16.597238+00	2022-09-20 08:39:16.597267+00	1	\N	\N	f	\N
85	CUSTOMER	customer	Matsumura Fishworks	11015	2022-09-20 08:39:16.597324+00	2022-09-20 08:39:16.597353+00	1	\N	\N	f	\N
86	CUSTOMER	customer	Omni Consumer Products	11016	2022-09-20 08:39:16.597522+00	2022-09-20 08:39:16.597553+00	1	\N	\N	f	\N
87	CUSTOMER	customer	Upton-Webber	11017	2022-09-20 08:39:16.597617+00	2022-09-20 08:39:16.597645+00	1	\N	\N	f	\N
88	CUSTOMER	customer	Grand Trunk Semaphore	11018	2022-09-20 08:39:16.597698+00	2022-09-20 08:39:16.597725+00	1	\N	\N	f	\N
89	CUSTOMER	customer	Ace Tomato	11019	2022-09-20 08:39:16.597778+00	2022-09-20 08:39:16.597806+00	1	\N	\N	f	\N
90	CUSTOMER	customer	Primatech Paper	11020	2022-09-20 08:39:16.597859+00	2022-09-20 08:39:16.597886+00	1	\N	\N	f	\N
91	CUSTOMER	customer	Universal Exports	11021	2022-09-20 08:39:16.597939+00	2022-09-20 08:39:16.597966+00	1	\N	\N	f	\N
92	CUSTOMER	customer	Duff	11022	2022-09-20 08:39:16.598019+00	2022-09-20 08:39:16.598046+00	1	\N	\N	f	\N
93	CUSTOMER	customer	Sunshine Desserts	11023	2022-09-20 08:39:16.598099+00	2022-09-20 08:39:16.598126+00	1	\N	\N	f	\N
94	CUSTOMER	customer	Paper Street Soap Co.	11024	2022-09-20 08:39:16.598179+00	2022-09-20 08:39:16.598206+00	1	\N	\N	f	\N
95	CUSTOMER	customer	Dunder Mifflin	11025	2022-09-20 08:39:16.598259+00	2022-09-20 08:39:16.598286+00	1	\N	\N	f	\N
96	CUSTOMER	customer	Wernham Hogg	11026	2022-09-20 08:39:16.59835+00	2022-09-20 08:39:16.598493+00	1	\N	\N	f	\N
97	CUSTOMER	customer	United Liberty Paper	11027	2022-09-20 08:39:16.598559+00	2022-09-20 08:39:16.598587+00	1	\N	\N	f	\N
98	CUSTOMER	customer	Union Aerospace Corporation	11028	2022-09-20 08:39:16.598642+00	2022-09-20 08:39:16.59867+00	1	\N	\N	f	\N
99	CUSTOMER	customer	Abstergo Industries	11029	2022-09-20 08:39:16.598723+00	2022-09-20 08:39:16.59875+00	1	\N	\N	f	\N
100	CUSTOMER	customer	Conglomerated Amalgamated	11030	2022-09-20 08:39:16.598803+00	2022-09-20 08:39:16.59883+00	1	\N	\N	f	\N
101	CUSTOMER	customer	CHOAM	11031	2022-09-20 08:39:16.598882+00	2022-09-20 08:39:16.59892+00	1	\N	\N	f	\N
102	CUSTOMER	customer	Cyberdyne Systems	11032	2022-09-20 08:39:16.598977+00	2022-09-20 08:39:16.599006+00	1	\N	\N	f	\N
103	CUSTOMER	customer	Digivation Industries	11033	2022-09-20 08:39:16.599062+00	2022-09-20 08:39:16.599102+00	1	\N	\N	f	\N
104	CUSTOMER	customer	Hishii Industries	11034	2022-09-20 08:39:16.599155+00	2022-09-20 08:39:16.599182+00	1	\N	\N	f	\N
105	CUSTOMER	customer	Nordyne Defense	11035	2022-09-20 08:39:16.599235+00	2022-09-20 08:39:16.599262+00	1	\N	\N	f	\N
106	CUSTOMER	customer	Ewing Oil	11036	2022-09-20 08:39:16.599315+00	2022-09-20 08:39:16.599342+00	1	\N	\N	f	\N
107	CUSTOMER	customer	Strickland Propane	11037	2022-09-20 08:39:16.599511+00	2022-09-20 08:39:16.599541+00	1	\N	\N	f	\N
108	CUSTOMER	customer	Benthic Petroleum	11038	2022-09-20 08:39:16.59959+00	2022-09-20 08:39:16.599611+00	1	\N	\N	f	\N
109	CUSTOMER	customer	Liandri Mining	11039	2022-09-20 08:39:16.599659+00	2022-09-20 08:39:16.599679+00	1	\N	\N	f	\N
110	CUSTOMER	customer	ENCOM	11040	2022-09-20 08:39:16.599734+00	2022-09-20 08:39:16.599753+00	1	\N	\N	f	\N
111	CUSTOMER	customer	Nakatomi Corporation	11041	2022-09-20 08:39:16.599791+00	2022-09-20 08:39:16.599811+00	1	\N	\N	f	\N
112	CUSTOMER	customer	Weyland-Yutani	11042	2022-09-20 08:39:16.599868+00	2022-09-20 08:39:16.599897+00	1	\N	\N	f	\N
113	CUSTOMER	customer	Bluth Company	11043	2022-09-20 08:39:16.61139+00	2022-09-20 08:39:16.611433+00	1	\N	\N	f	\N
114	CUSTOMER	customer	Devlin MacGregor	11044	2022-09-20 08:39:16.611493+00	2022-09-20 08:39:16.611523+00	1	\N	\N	f	\N
115	CUSTOMER	customer	Dharma Initiative	11045	2022-09-20 08:39:16.611581+00	2022-09-20 08:39:16.61161+00	1	\N	\N	f	\N
116	CUSTOMER	customer	Ecumena	11046	2022-09-20 08:39:16.611667+00	2022-09-20 08:39:16.611697+00	1	\N	\N	f	\N
117	CUSTOMER	customer	Hanso Foundation	11047	2022-09-20 08:39:16.611754+00	2022-09-20 08:39:16.611784+00	1	\N	\N	f	\N
118	CUSTOMER	customer	InGen	11048	2022-09-20 08:39:16.611844+00	2022-09-20 08:39:16.611874+00	1	\N	\N	f	\N
119	CUSTOMER	customer	Khumalo	11049	2022-09-20 08:39:16.611934+00	2022-09-20 08:39:16.611965+00	1	\N	\N	f	\N
120	CUSTOMER	customer	Medical Mechanica	11050	2022-09-20 08:39:16.612046+00	2022-09-20 08:39:16.612077+00	1	\N	\N	f	\N
121	CUSTOMER	customer	N.E.R.D.	11051	2022-09-20 08:39:16.612134+00	2022-09-20 08:39:16.612164+00	1	\N	\N	f	\N
122	CUSTOMER	customer	North Central Positronics	11052	2022-09-20 08:39:16.61222+00	2022-09-20 08:39:16.61225+00	1	\N	\N	f	\N
123	CUSTOMER	customer	Prescott Pharmaceuticals	11053	2022-09-20 08:39:16.612306+00	2022-09-20 08:39:16.612335+00	1	\N	\N	f	\N
124	CUSTOMER	customer	Tricell	11054	2022-09-20 08:39:16.612391+00	2022-09-20 08:39:16.612421+00	1	\N	\N	f	\N
125	CUSTOMER	customer	Umbrella Corporation	11055	2022-09-20 08:39:16.612478+00	2022-09-20 08:39:16.612508+00	1	\N	\N	f	\N
126	CUSTOMER	customer	VersaLife Corporation	11056	2022-09-20 08:39:16.612565+00	2022-09-20 08:39:16.612595+00	1	\N	\N	f	\N
127	CUSTOMER	customer	Optican	11057	2022-09-20 08:39:16.612651+00	2022-09-20 08:39:16.61268+00	1	\N	\N	f	\N
128	CUSTOMER	customer	Rossum Corporation	11058	2022-09-20 08:39:16.612736+00	2022-09-20 08:39:16.612765+00	1	\N	\N	f	\N
129	CUSTOMER	customer	Simeon	11059	2022-09-20 08:39:16.612821+00	2022-09-20 08:39:16.61285+00	1	\N	\N	f	\N
130	CUSTOMER	customer	Ziodex Industries	11060	2022-09-20 08:39:16.612906+00	2022-09-20 08:39:16.612935+00	1	\N	\N	f	\N
131	CUSTOMER	customer	Metacortex	11061	2022-09-20 08:39:16.612991+00	2022-09-20 08:39:16.61302+00	1	\N	\N	f	\N
132	CUSTOMER	customer	Delos	11062	2022-09-20 08:39:16.613076+00	2022-09-20 08:39:16.613105+00	1	\N	\N	f	\N
133	CUSTOMER	customer	Deon International	11063	2022-09-20 08:39:16.613162+00	2022-09-20 08:39:16.613191+00	1	\N	\N	f	\N
134	CUSTOMER	customer	Edgars	11064	2022-09-20 08:39:16.61327+00	2022-09-20 08:39:16.613301+00	1	\N	\N	f	\N
135	CUSTOMER	customer	Global Dynamics	11065	2022-09-20 08:39:16.613362+00	2022-09-20 08:39:16.613374+00	1	\N	\N	f	\N
136	CUSTOMER	customer	LexCorp	11066	2022-09-20 08:39:16.613421+00	2022-09-20 08:39:16.61345+00	1	\N	\N	f	\N
137	CUSTOMER	customer	Mishima Zaibatsu	11067	2022-09-20 08:39:16.613701+00	2022-09-20 08:39:16.613758+00	1	\N	\N	f	\N
138	CUSTOMER	customer	OsCorp	11068	2022-09-20 08:39:16.61399+00	2022-09-20 08:39:16.61404+00	1	\N	\N	f	\N
139	CUSTOMER	customer	Universal Terraforming	11069	2022-09-20 08:39:16.614137+00	2022-09-20 08:39:16.61433+00	1	\N	\N	f	\N
140	CUSTOMER	customer	Wayne Enterprises	11070	2022-09-20 08:39:16.614431+00	2022-09-20 08:39:16.614473+00	1	\N	\N	f	\N
141	CUSTOMER	customer	McCandless Communications	11071	2022-09-20 08:39:16.614569+00	2022-09-20 08:39:16.614611+00	1	\N	\N	f	\N
142	CUSTOMER	customer	Parrish Communications	11072	2022-09-20 08:39:16.614703+00	2022-09-20 08:39:16.614743+00	1	\N	\N	f	\N
143	CUSTOMER	customer	Network23	11073	2022-09-20 08:39:16.614829+00	2022-09-20 08:39:16.61487+00	1	\N	\N	f	\N
144	CUSTOMER	customer	Astromech	11074	2022-09-20 08:39:16.614955+00	2022-09-20 08:39:16.614994+00	1	\N	\N	f	\N
145	CUSTOMER	customer	Capsule	11075	2022-09-20 08:39:16.615077+00	2022-09-20 08:39:16.615117+00	1	\N	\N	f	\N
146	CUSTOMER	customer	Tyrell Corp.	11076	2022-09-20 08:39:16.6152+00	2022-09-20 08:39:16.615239+00	1	\N	\N	f	\N
147	CUSTOMER	customer	United Robotronics	11077	2022-09-20 08:39:16.615303+00	2022-09-20 08:39:16.615332+00	1	\N	\N	f	\N
148	CUSTOMER	customer	NorthAm Robotics	11078	2022-09-20 08:39:16.615389+00	2022-09-20 08:39:16.615418+00	1	\N	\N	f	\N
149	CUSTOMER	customer	Serrano Genomics	11079	2022-09-20 08:39:16.615475+00	2022-09-20 08:39:16.615504+00	1	\N	\N	f	\N
150	CUSTOMER	customer	Ajax	11080	2022-09-20 08:39:16.615561+00	2022-09-20 08:39:16.61559+00	1	\N	\N	f	\N
151	CUSTOMER	customer	Cym Labs	11081	2022-09-20 08:39:16.615646+00	2022-09-20 08:39:16.615675+00	1	\N	\N	f	\N
152	CUSTOMER	customer	Ovi	11082	2022-09-20 08:39:16.61573+00	2022-09-20 08:39:16.615759+00	1	\N	\N	f	\N
153	CUSTOMER	customer	Aperture Science	11083	2022-09-20 08:39:16.615816+00	2022-09-20 08:39:16.615845+00	1	\N	\N	f	\N
154	CUSTOMER	customer	DataDyne	11084	2022-09-20 08:39:16.615901+00	2022-09-20 08:39:16.61593+00	1	\N	\N	f	\N
155	CUSTOMER	customer	Dynatechnics	11085	2022-09-20 08:39:16.615985+00	2022-09-20 08:39:16.616014+00	1	\N	\N	f	\N
156	CUSTOMER	customer	Izon	11086	2022-09-20 08:39:16.616071+00	2022-09-20 08:39:16.6161+00	1	\N	\N	f	\N
157	CUSTOMER	customer	Seburo	11087	2022-09-20 08:39:16.616156+00	2022-09-20 08:39:16.616185+00	1	\N	\N	f	\N
158	CUSTOMER	customer	Stark Industries	11088	2022-09-20 08:39:16.616242+00	2022-09-20 08:39:16.616271+00	1	\N	\N	f	\N
159	CUSTOMER	customer	X-Com	11089	2022-09-20 08:39:16.616328+00	2022-09-20 08:39:16.616357+00	1	\N	\N	f	\N
160	CUSTOMER	customer	Cathedral Software	11090	2022-09-20 08:39:16.616415+00	2022-09-20 08:39:16.616445+00	1	\N	\N	f	\N
161	CUSTOMER	customer	ComTron	11091	2022-09-20 08:39:16.616501+00	2022-09-20 08:39:16.61653+00	1	\N	\N	f	\N
162	CUSTOMER	customer	Uplink	11092	2022-09-20 08:39:16.616586+00	2022-09-20 08:39:16.616615+00	1	\N	\N	f	\N
163	CUSTOMER	customer	Globochem	11093	2022-09-20 08:39:16.649016+00	2022-09-20 08:39:16.649065+00	1	\N	\N	f	\N
164	CUSTOMER	customer	Grayson Sky Domes	11094	2022-09-20 08:39:16.649139+00	2022-09-20 08:39:16.649171+00	1	\N	\N	f	\N
165	CUSTOMER	customer	Monsters, Inc.	11095	2022-09-20 08:39:16.649239+00	2022-09-20 08:39:16.649503+00	1	\N	\N	f	\N
166	CUSTOMER	customer	Stay Puft	11096	2022-09-20 08:39:16.649605+00	2022-09-20 08:39:16.649637+00	1	\N	\N	f	\N
167	CUSTOMER	customer	Soylent Corporation	11097	2022-09-20 08:39:16.649702+00	2022-09-20 08:39:16.649731+00	1	\N	\N	f	\N
168	CUSTOMER	customer	Allied British Plastics	11098	2022-09-20 08:39:16.649793+00	2022-09-20 08:39:16.649822+00	1	\N	\N	f	\N
169	CUSTOMER	customer	Vandelay Industries	11099	2022-09-20 08:39:16.64988+00	2022-09-20 08:39:16.649909+00	1	\N	\N	f	\N
170	CUSTOMER	customer	The android's Dungeon	11100	2022-09-20 08:39:16.649965+00	2022-09-20 08:39:16.649994+00	1	\N	\N	f	\N
171	CUSTOMER	customer	Kwik-E-Mart	11101	2022-09-20 08:39:16.65005+00	2022-09-20 08:39:16.650079+00	1	\N	\N	f	\N
172	CUSTOMER	customer	Mega Lo Mart	11102	2022-09-20 08:39:16.650136+00	2022-09-20 08:39:16.650165+00	1	\N	\N	f	\N
173	CUSTOMER	customer	Zimms	11103	2022-09-20 08:39:16.650221+00	2022-09-20 08:39:16.65025+00	1	\N	\N	f	\N
174	CUSTOMER	customer	Treadstone	11104	2022-09-20 08:39:16.650306+00	2022-09-20 08:39:16.650335+00	1	\N	\N	f	\N
175	CUSTOMER	customer	Interplanetary Expeditions	11105	2022-09-20 08:39:16.650656+00	2022-09-20 08:39:16.65069+00	1	\N	\N	f	\N
176	CUSTOMER	customer	Trade Federation	11106	2022-09-20 08:39:16.650751+00	2022-09-20 08:39:16.65078+00	1	\N	\N	f	\N
177	CUSTOMER	customer	Veridian Dynamics	11107	2022-09-20 08:39:16.650839+00	2022-09-20 08:39:16.650869+00	1	\N	\N	f	\N
178	CUSTOMER	customer	Yoyodyne Propulsion	11108	2022-09-20 08:39:16.650927+00	2022-09-20 08:39:16.650956+00	1	\N	\N	f	\N
179	CUSTOMER	customer	IPS	11109	2022-09-20 08:39:16.651014+00	2022-09-20 08:39:16.651043+00	1	\N	\N	f	\N
180	CUSTOMER	customer	Fuji Air	11110	2022-09-20 08:39:16.6511+00	2022-09-20 08:39:16.651129+00	1	\N	\N	f	\N
181	CUSTOMER	customer	Ajira Airways	11111	2022-09-20 08:39:16.651186+00	2022-09-20 08:39:16.651215+00	1	\N	\N	f	\N
182	CUSTOMER	customer	Roxxon	11112	2022-09-20 08:39:16.651273+00	2022-09-20 08:39:16.651302+00	1	\N	\N	f	\N
183	CUSTOMER	customer	Shinra Electric	11113	2022-09-20 08:39:16.651631+00	2022-09-20 08:39:16.651744+00	1	\N	\N	f	\N
184	CUSTOMER	customer	TriOptimum	11114	2022-09-20 08:39:16.651996+00	2022-09-20 08:39:16.652098+00	1	\N	\N	f	\N
185	CUSTOMER	customer	TetraCorp	11115	2022-09-20 08:39:16.653406+00	2022-09-20 08:39:16.654714+00	1	\N	\N	f	\N
186	CUSTOMER	customer	Ultor	11116	2022-09-20 08:39:16.654879+00	2022-09-20 08:39:16.654917+00	1	\N	\N	f	\N
187	CUSTOMER	customer	U-North	11117	2022-09-20 08:39:16.654991+00	2022-09-20 08:39:16.655023+00	1	\N	\N	f	\N
188	CUSTOMER	customer	Intelligent Audit	11118	2022-09-20 08:39:16.655089+00	2022-09-20 08:39:16.655119+00	1	\N	\N	f	\N
189	CUSTOMER	customer	Been Verified	11119	2022-09-20 08:39:16.655181+00	2022-09-20 08:39:16.655211+00	1	\N	\N	f	\N
190	CUSTOMER	customer	Sailthru	11120	2022-09-20 08:39:16.655503+00	2022-09-20 08:39:16.655545+00	1	\N	\N	f	\N
191	CUSTOMER	customer	YellowHammer	11121	2022-09-20 08:39:16.655621+00	2022-09-20 08:39:16.655652+00	1	\N	\N	f	\N
192	CUSTOMER	customer	Conductor	11122	2022-09-20 08:39:16.655716+00	2022-09-20 08:39:16.655745+00	1	\N	\N	f	\N
193	CUSTOMER	customer	Cinium Financial Services	11123	2022-09-20 08:39:16.655807+00	2022-09-20 08:39:16.655836+00	1	\N	\N	f	\N
194	CUSTOMER	customer	33Across	11124	2022-09-20 08:39:16.655896+00	2022-09-20 08:39:16.655925+00	1	\N	\N	f	\N
195	CUSTOMER	customer	Live With Intention	11125	2022-09-20 08:39:16.655984+00	2022-09-20 08:39:16.656014+00	1	\N	\N	f	\N
196	CUSTOMER	customer	Quantum Networks	11126	2022-09-20 08:39:16.656071+00	2022-09-20 08:39:16.656101+00	1	\N	\N	f	\N
197	CUSTOMER	customer	Renegade Furniture Group	11127	2022-09-20 08:39:16.656158+00	2022-09-20 08:39:16.657675+00	1	\N	\N	f	\N
198	CUSTOMER	customer	Gilead Sciences	11128	2022-09-20 08:39:16.657872+00	2022-09-20 08:39:16.657918+00	1	\N	\N	f	\N
199	CUSTOMER	customer	Cymer	11129	2022-09-20 08:39:16.657999+00	2022-09-20 08:39:16.658118+00	1	\N	\N	f	\N
200	CUSTOMER	customer	BuddyTV	11130	2022-09-20 08:39:16.658203+00	2022-09-20 08:39:16.658231+00	1	\N	\N	f	\N
201	CUSTOMER	customer	The HCI Group	11131	2022-09-20 08:39:16.658285+00	2022-09-20 08:39:16.658325+00	1	\N	\N	f	\N
202	CUSTOMER	customer	KENTECH Consulting	11132	2022-09-20 08:39:16.658513+00	2022-09-20 08:39:16.658541+00	1	\N	\N	f	\N
203	CUSTOMER	customer	Column Five	11133	2022-09-20 08:39:16.658594+00	2022-09-20 08:39:16.658622+00	1	\N	\N	f	\N
204	CUSTOMER	customer	GSATi	11134	2022-09-20 08:39:16.658674+00	2022-09-20 08:39:16.658702+00	1	\N	\N	f	\N
205	CUSTOMER	customer	ThinkLite	11135	2022-09-20 08:39:16.658755+00	2022-09-20 08:39:16.658782+00	1	\N	\N	f	\N
206	CUSTOMER	customer	Bottle Rocket Apps	11136	2022-09-20 08:39:16.658835+00	2022-09-20 08:39:16.658863+00	1	\N	\N	f	\N
207	CUSTOMER	customer	Dhaliwal Labs	11137	2022-09-20 08:39:16.658916+00	2022-09-20 08:39:16.658944+00	1	\N	\N	f	\N
208	CUSTOMER	customer	Brant, Agron, Meiselman	11138	2022-09-20 08:39:16.658997+00	2022-09-20 08:39:16.659025+00	1	\N	\N	f	\N
209	CUSTOMER	customer	Insurance Megacorp	11139	2022-09-20 08:39:16.659077+00	2022-09-20 08:39:16.659105+00	1	\N	\N	f	\N
210	CUSTOMER	customer	Bledsoe Cathcart Diestel and Pedersen LLP	11140	2022-09-20 08:39:16.659158+00	2022-09-20 08:39:16.659186+00	1	\N	\N	f	\N
211	CUSTOMER	customer	Cuna Mutual Insurance Society	11141	2022-09-20 08:39:16.659239+00	2022-09-20 08:39:16.659266+00	1	\N	\N	f	\N
212	CUSTOMER	customer	Augusta Medical Associates	11142	2022-09-20 08:39:16.659541+00	2022-09-20 08:39:16.65957+00	1	\N	\N	f	\N
213	CUSTOMER	customer	Cardiovascular Disease Special	11143	2022-09-20 08:39:16.676865+00	2022-09-20 08:39:16.676919+00	1	\N	\N	f	\N
214	CUSTOMER	customer	Pediatric Subspecialty Faculty	11144	2022-09-20 08:39:16.676992+00	2022-09-20 08:39:16.677016+00	1	\N	\N	f	\N
215	CUSTOMER	customer	Mensa, Ltd.	11145	2022-09-20 08:39:16.677072+00	2022-09-20 08:39:16.677106+00	1	\N	\N	f	\N
216	CUSTOMER	customer	South Bay Medical Center	11146	2022-09-20 08:39:16.677613+00	2022-09-20 08:39:16.677645+00	1	\N	\N	f	\N
217	CUSTOMER	customer	United Methodist Communications	11147	2022-09-20 08:39:16.677695+00	2022-09-20 08:39:16.677748+00	1	\N	\N	f	\N
218	CUSTOMER	customer	Oakland County Community Mental Health	11148	2022-09-20 08:39:16.677898+00	2022-09-20 08:39:16.677928+00	1	\N	\N	f	\N
219	CUSTOMER	customer	Arkansas Blue Cross and Blue Shield	11149	2022-09-20 08:39:16.677973+00	2022-09-20 08:39:16.677986+00	1	\N	\N	f	\N
220	CUSTOMER	customer	Piggly Wiggly Carolina Co.	11150	2022-09-20 08:39:16.678032+00	2022-09-20 08:39:16.678177+00	1	\N	\N	f	\N
221	CUSTOMER	customer	Woodlands Medical Group	11151	2022-09-20 08:39:16.67823+00	2022-09-20 08:39:16.678251+00	1	\N	\N	f	\N
222	CUSTOMER	customer	Arbitration Association	11152	2022-09-20 08:39:16.678309+00	2022-09-20 08:39:16.678338+00	1	\N	\N	f	\N
223	CUSTOMER	customer	Talcomp Management Services	11153	2022-09-20 08:39:16.678785+00	2022-09-20 08:39:16.678807+00	1	\N	\N	f	\N
224	CUSTOMER	customer	Denticare Of Oklahoma	11154	2022-09-20 08:39:16.678862+00	2022-09-20 08:39:16.678896+00	1	\N	\N	f	\N
225	CUSTOMER	customer	Gulf States Paper Corporation	11155	2022-09-20 08:39:16.67899+00	2022-09-20 08:39:16.679016+00	1	\N	\N	f	\N
226	CUSTOMER	customer	Oncolytics Biotech Inc.	11156	2022-09-20 08:39:16.679066+00	2022-09-20 08:39:16.679099+00	1	\N	\N	f	\N
227	CUSTOMER	customer	Pacificare Health Systems Az	11157	2022-09-20 08:39:16.679153+00	2022-09-20 08:39:16.679174+00	1	\N	\N	f	\N
228	CUSTOMER	customer	Southern Orthopedics	11158	2022-09-20 08:39:16.679344+00	2022-09-20 08:39:16.679434+00	1	\N	\N	f	\N
229	CUSTOMER	customer	News Day	11159	2022-09-20 08:39:16.679517+00	2022-09-20 08:39:16.679548+00	1	\N	\N	f	\N
230	CUSTOMER	customer	Quallaby Corporation	11160	2022-09-20 08:39:16.679599+00	2022-09-20 08:39:16.67962+00	1	\N	\N	f	\N
231	CUSTOMER	customer	Computer Sciences Corporation	11161	2022-09-20 08:39:16.679703+00	2022-09-20 08:39:16.679794+00	1	\N	\N	f	\N
232	CUSTOMER	customer	Premier Inc	11162	2022-09-20 08:39:16.679845+00	2022-09-20 08:39:16.679877+00	1	\N	\N	f	\N
233	CUSTOMER	customer	Innova Solutions	11163	2022-09-20 08:39:16.679935+00	2022-09-20 08:39:16.67997+00	1	\N	\N	f	\N
234	CUSTOMER	customer	Medical Research Technologies	11164	2022-09-20 08:39:16.680013+00	2022-09-20 08:39:16.680102+00	1	\N	\N	f	\N
235	CUSTOMER	customer	Spine Rehab Center	11165	2022-09-20 08:39:16.680168+00	2022-09-20 08:39:16.680302+00	1	\N	\N	f	\N
236	CUSTOMER	customer	CGH Medical Center	11166	2022-09-20 08:39:16.680361+00	2022-09-20 08:39:16.680397+00	1	\N	\N	f	\N
237	CUSTOMER	customer	Olin Corporation	11167	2022-09-20 08:39:16.680457+00	2022-09-20 08:39:16.680514+00	1	\N	\N	f	\N
238	CUSTOMER	customer	Sempra Energy	11168	2022-09-20 08:39:16.680572+00	2022-09-20 08:39:16.68061+00	1	\N	\N	f	\N
239	CUSTOMER	customer	PA Neurosurgery and Neuroscience	11169	2022-09-20 08:39:16.680692+00	2022-09-20 08:39:16.680899+00	1	\N	\N	f	\N
240	CUSTOMER	customer	West Oak Capital Group Inc	11170	2022-09-20 08:39:16.680957+00	2022-09-20 08:39:16.680979+00	1	\N	\N	f	\N
241	CUSTOMER	customer	Titanium Corporation Inc.	11171	2022-09-20 08:39:16.681034+00	2022-09-20 08:39:16.681053+00	1	\N	\N	f	\N
242	CUSTOMER	customer	Creative Healthcare	11172	2022-09-20 08:39:16.681098+00	2022-09-20 08:39:16.681128+00	1	\N	\N	f	\N
243	CUSTOMER	customer	Georgia Power Company	11173	2022-09-20 08:39:16.681182+00	2022-09-20 08:39:16.681319+00	1	\N	\N	f	\N
244	CUSTOMER	customer	Atlanta Integrative Medicine	11174	2022-09-20 08:39:16.681377+00	2022-09-20 08:39:16.681404+00	1	\N	\N	f	\N
245	CUSTOMER	customer	Heart and Vascular Clinic	11175	2022-09-20 08:39:16.681504+00	2022-09-20 08:39:16.68153+00	1	\N	\N	f	\N
246	CUSTOMER	customer	Compass Investment Partners	11176	2022-09-20 08:39:16.681579+00	2022-09-20 08:39:16.681608+00	1	\N	\N	f	\N
247	CUSTOMER	customer	CDC Ixis North America Inc.	11177	2022-09-20 08:39:16.682389+00	2022-09-20 08:39:16.682427+00	1	\N	\N	f	\N
248	CUSTOMER	customer	James Mintz Group, Inc.	11178	2022-09-20 08:39:16.68249+00	2022-09-20 08:39:16.682521+00	1	\N	\N	f	\N
249	CUSTOMER	customer	Stoxnetwork Corporation	11179	2022-09-20 08:39:16.68258+00	2022-09-20 08:39:16.682603+00	1	\N	\N	f	\N
250	CUSTOMER	customer	Kansas City Power and Light Co.	11180	2022-09-20 08:39:16.682666+00	2022-09-20 08:39:16.682689+00	1	\N	\N	f	\N
251	CUSTOMER	customer	Bella Technologies	11181	2022-09-20 08:39:16.682752+00	2022-09-20 08:39:16.682772+00	1	\N	\N	f	\N
252	CUSTOMER	customer	Naples Pediatrics	11182	2022-09-20 08:39:16.682814+00	2022-09-20 08:39:16.682843+00	1	\N	\N	f	\N
253	CUSTOMER	customer	Intrepid Minerals Corporation	11183	2022-09-20 08:39:16.682909+00	2022-09-20 08:39:16.682932+00	1	\N	\N	f	\N
254	CUSTOMER	customer	Wauwatosa Medical Group	11184	2022-09-20 08:39:16.682996+00	2022-09-20 08:39:16.683019+00	1	\N	\N	f	\N
255	CUSTOMER	customer	Carolina Health Centers, Inc.	11185	2022-09-20 08:39:16.683331+00	2022-09-20 08:39:16.683386+00	1	\N	\N	f	\N
256	CUSTOMER	customer	Chevron Texaco	11186	2022-09-20 08:39:16.683457+00	2022-09-20 08:39:16.683512+00	1	\N	\N	f	\N
257	CUSTOMER	customer	Orchard Group	11187	2022-09-20 08:39:16.683878+00	2022-09-20 08:39:16.683938+00	1	\N	\N	f	\N
258	CUSTOMER	customer	Copper Ab	11188	2022-09-20 08:39:16.684012+00	2022-09-20 08:39:16.684034+00	1	\N	\N	f	\N
259	CUSTOMER	customer	The Vanguard Group, Inc.	11189	2022-09-20 08:39:16.684127+00	2022-09-20 08:39:16.684151+00	1	\N	\N	f	\N
260	CUSTOMER	customer	Citizens Communications	11190	2022-09-20 08:39:16.6842+00	2022-09-20 08:39:16.684418+00	1	\N	\N	f	\N
261	CUSTOMER	customer	Transnet	14001	2022-09-20 08:39:16.684477+00	2022-09-20 08:39:16.6845+00	1	\N	\N	f	\N
262	CUSTOMER	customer	3Way International Logistics	14002	2022-09-20 08:39:16.684556+00	2022-09-20 08:39:16.684588+00	1	\N	\N	f	\N
263	CUSTOMER	customer	Ache Records	14003	2022-09-20 08:39:16.726438+00	2022-09-20 08:39:16.726499+00	1	\N	\N	f	\N
264	CUSTOMER	customer	Advanced Cyclotron Systems	14004	2022-09-20 08:39:16.726583+00	2022-09-20 08:39:16.726632+00	1	\N	\N	f	\N
265	CUSTOMER	customer	Aldo Group	14005	2022-09-20 08:39:16.726709+00	2022-09-20 08:39:16.726744+00	1	\N	\N	f	\N
266	CUSTOMER	customer	Algonquin Power and Utilities	14006	2022-09-20 08:39:16.726834+00	2022-09-20 08:39:16.727678+00	1	\N	\N	f	\N
267	CUSTOMER	customer	Angoss	14007	2022-09-20 08:39:16.728438+00	2022-09-20 08:39:16.72851+00	1	\N	\N	f	\N
268	CUSTOMER	customer	Appnovation	14008	2022-09-20 08:39:16.728598+00	2022-09-20 08:39:16.728622+00	1	\N	\N	f	\N
269	CUSTOMER	customer	Army and Navy Stores	14009	2022-09-20 08:39:16.728695+00	2022-09-20 08:39:16.728727+00	1	\N	\N	f	\N
270	CUSTOMER	customer	ATB Financial	14010	2022-09-20 08:39:16.728786+00	2022-09-20 08:39:16.728816+00	1	\N	\N	f	\N
271	CUSTOMER	customer	Banff Lodging Co	14011	2022-09-20 08:39:16.728869+00	2022-09-20 08:39:16.72889+00	1	\N	\N	f	\N
272	CUSTOMER	customer	Bard Ventures	14012	2022-09-20 08:39:16.728928+00	2022-09-20 08:39:16.728948+00	1	\N	\N	f	\N
273	CUSTOMER	customer	BC Research	14013	2022-09-20 08:39:16.729058+00	2022-09-20 08:39:16.729104+00	1	\N	\N	f	\N
274	CUSTOMER	customer	Bell Canada	14014	2022-09-20 08:39:16.729845+00	2022-09-20 08:39:16.729929+00	1	\N	\N	f	\N
275	CUSTOMER	customer	Big Blue Bubble	14015	2022-09-20 08:39:16.730081+00	2022-09-20 08:39:16.730123+00	1	\N	\N	f	\N
276	CUSTOMER	customer	Biovail	14016	2022-09-20 08:39:16.730391+00	2022-09-20 08:39:16.730444+00	1	\N	\N	f	\N
277	CUSTOMER	customer	Black Hen Music	14017	2022-09-20 08:39:16.730517+00	2022-09-20 08:39:16.730746+00	1	\N	\N	f	\N
278	CUSTOMER	customer	BlackBerry Limited	14018	2022-09-20 08:39:16.73083+00	2022-09-20 08:39:16.730857+00	1	\N	\N	f	\N
279	CUSTOMER	customer	Blenz Coffee	14019	2022-09-20 08:39:16.730907+00	2022-09-20 08:39:16.730937+00	1	\N	\N	f	\N
280	CUSTOMER	customer	Boeing Canada	14020	2022-09-20 08:39:16.731002+00	2022-09-20 08:39:16.73103+00	1	\N	\N	f	\N
281	CUSTOMER	customer	Boston Pizza	14021	2022-09-20 08:39:16.731093+00	2022-09-20 08:39:16.731126+00	1	\N	\N	f	\N
282	CUSTOMER	customer	Bowring Brothers	14022	2022-09-20 08:39:16.731788+00	2022-09-20 08:39:16.731829+00	1	\N	\N	f	\N
283	CUSTOMER	customer	BrightSide Technologies	14023	2022-09-20 08:39:16.73189+00	2022-09-20 08:39:16.73192+00	1	\N	\N	f	\N
284	CUSTOMER	customer	Bruce Power	14024	2022-09-20 08:39:16.731977+00	2022-09-20 08:39:16.732006+00	1	\N	\N	f	\N
285	CUSTOMER	customer	Bullfrog Power	14025	2022-09-20 08:39:16.732062+00	2022-09-20 08:39:16.732092+00	1	\N	\N	f	\N
286	CUSTOMER	customer	Cadillac Fairview	14026	2022-09-20 08:39:16.732148+00	2022-09-20 08:39:16.732178+00	1	\N	\N	f	\N
287	CUSTOMER	customer	Canada Deposit Insurance Corporation	14027	2022-09-20 08:39:16.732381+00	2022-09-20 08:39:16.732422+00	1	\N	\N	f	\N
288	CUSTOMER	customer	Canadian Bank Note Company	14028	2022-09-20 08:39:16.732495+00	2022-09-20 08:39:16.732534+00	1	\N	\N	f	\N
289	CUSTOMER	customer	Canadian Light Source	14029	2022-09-20 08:39:16.732612+00	2022-09-20 08:39:16.732653+00	1	\N	\N	f	\N
290	CUSTOMER	customer	Canadian Natural Resources	14030	2022-09-20 08:39:16.732741+00	2022-09-20 08:39:16.732773+00	1	\N	\N	f	\N
291	CUSTOMER	customer	Canadian Steamship Lines	14031	2022-09-20 08:39:16.73283+00	2022-09-20 08:39:16.73286+00	1	\N	\N	f	\N
292	CUSTOMER	customer	Canadian Tire Bank	14032	2022-09-20 08:39:16.732916+00	2022-09-20 08:39:16.732945+00	1	\N	\N	f	\N
293	CUSTOMER	customer	Candente Copper	14033	2022-09-20 08:39:16.733+00	2022-09-20 08:39:16.73304+00	1	\N	\N	f	\N
294	CUSTOMER	customer	CanJet	14034	2022-09-20 08:39:16.733122+00	2022-09-20 08:39:16.733163+00	1	\N	\N	f	\N
295	CUSTOMER	customer	Capcom Vancouver	14035	2022-09-20 08:39:16.733364+00	2022-09-20 08:39:16.733397+00	1	\N	\N	f	\N
296	CUSTOMER	customer	Casavant Frares	14036	2022-09-20 08:39:16.733456+00	2022-09-20 08:39:16.733485+00	1	\N	\N	f	\N
297	CUSTOMER	customer	Cellcom Communications	14037	2022-09-20 08:39:16.733541+00	2022-09-20 08:39:16.733571+00	1	\N	\N	f	\N
298	CUSTOMER	customer	Centra Gas Manitoba Inc.	14038	2022-09-20 08:39:16.733627+00	2022-09-20 08:39:16.733656+00	1	\N	\N	f	\N
299	CUSTOMER	customer	Chapters	14039	2022-09-20 08:39:16.733712+00	2022-09-20 08:39:16.733741+00	1	\N	\N	f	\N
300	CUSTOMER	customer	Choices Market	14040	2022-09-20 08:39:16.733798+00	2022-09-20 08:39:16.733838+00	1	\N	\N	f	\N
301	CUSTOMER	customer	Cirque du Soleil	14041	2022-09-20 08:39:16.73391+00	2022-09-20 08:39:16.733945+00	1	\N	\N	f	\N
302	CUSTOMER	customer	Coachman Insurance Company	14042	2022-09-20 08:39:16.734004+00	2022-09-20 08:39:16.734033+00	1	\N	\N	f	\N
303	CUSTOMER	customer	Comm100	14043	2022-09-20 08:39:16.73409+00	2022-09-20 08:39:16.734119+00	1	\N	\N	f	\N
304	CUSTOMER	customer	Conestoga-Rovers and Associates	14044	2022-09-20 08:39:16.734175+00	2022-09-20 08:39:16.734204+00	1	\N	\N	f	\N
305	CUSTOMER	customer	Cordiant Capital Inc.	14045	2022-09-20 08:39:16.734259+00	2022-09-20 08:39:16.734288+00	1	\N	\N	f	\N
306	CUSTOMER	customer	Corus Entertainment	14046	2022-09-20 08:39:16.734344+00	2022-09-20 08:39:16.734373+00	1	\N	\N	f	\N
307	CUSTOMER	customer	Country Style	14047	2022-09-20 08:39:16.734545+00	2022-09-20 08:39:16.734576+00	1	\N	\N	f	\N
308	CUSTOMER	customer	Crestline Coach	14048	2022-09-20 08:39:16.734625+00	2022-09-20 08:39:16.734646+00	1	\N	\N	f	\N
309	CUSTOMER	customer	CTV Television Network	14049	2022-09-20 08:39:16.734703+00	2022-09-20 08:39:16.734749+00	1	\N	\N	f	\N
310	CUSTOMER	customer	Cymax Stores	14050	2022-09-20 08:39:16.735675+00	2022-09-20 08:39:16.735735+00	1	\N	\N	f	\N
311	CUSTOMER	customer	Dare Foods	14051	2022-09-20 08:39:16.738506+00	2022-09-20 08:39:16.738616+00	1	\N	\N	f	\N
312	CUSTOMER	customer	Delta Hotels	14052	2022-09-20 08:39:16.738945+00	2022-09-20 08:39:16.739017+00	1	\N	\N	f	\N
313	CUSTOMER	customer	Digital Extremes	14053	2022-09-20 08:39:16.755505+00	2022-09-20 08:39:16.755553+00	1	\N	\N	f	\N
314	CUSTOMER	customer	Discovery Air Defence	14054	2022-09-20 08:39:16.755653+00	2022-09-20 08:39:16.755783+00	1	\N	\N	f	\N
315	CUSTOMER	customer	Dominion Voting Systems	14055	2022-09-20 08:39:16.755916+00	2022-09-20 08:39:16.755963+00	1	\N	\N	f	\N
316	CUSTOMER	customer	Donner Metals	14056	2022-09-20 08:39:16.756291+00	2022-09-20 08:39:16.756329+00	1	\N	\N	f	\N
317	CUSTOMER	customer	Dynamsoft	14057	2022-09-20 08:39:16.756399+00	2022-09-20 08:39:16.756422+00	1	\N	\N	f	\N
318	CUSTOMER	customer	EA Black Box	14058	2022-09-20 08:39:16.756805+00	2022-09-20 08:39:16.756846+00	1	\N	\N	f	\N
319	CUSTOMER	customer	Electrohome	14059	2022-09-20 08:39:16.756918+00	2022-09-20 08:39:16.756954+00	1	\N	\N	f	\N
320	CUSTOMER	customer	Emera	14060	2022-09-20 08:39:16.757661+00	2022-09-20 08:39:16.757873+00	1	\N	\N	f	\N
321	CUSTOMER	customer	Enwave	14061	2022-09-20 08:39:16.758023+00	2022-09-20 08:39:16.75806+00	1	\N	\N	f	\N
322	CUSTOMER	customer	FandP Manufacturing Inc.	14062	2022-09-20 08:39:16.758129+00	2022-09-20 08:39:16.75816+00	1	\N	\N	f	\N
323	CUSTOMER	customer	Fairmont Hotels and Resorts	14063	2022-09-20 08:39:16.758222+00	2022-09-20 08:39:16.758252+00	1	\N	\N	f	\N
324	CUSTOMER	customer	Farmers of North America	14064	2022-09-20 08:39:16.758313+00	2022-09-20 08:39:16.758343+00	1	\N	\N	f	\N
325	CUSTOMER	customer	Fido Solutions	14065	2022-09-20 08:39:16.758402+00	2022-09-20 08:39:16.758431+00	1	\N	\N	f	\N
326	CUSTOMER	customer	First Air	14066	2022-09-20 08:39:16.758489+00	2022-09-20 08:39:16.758518+00	1	\N	\N	f	\N
327	CUSTOMER	customer	Flickr	14067	2022-09-20 08:39:16.758575+00	2022-09-20 08:39:16.758604+00	1	\N	\N	f	\N
328	CUSTOMER	customer	Ford Motor Company of Canada	14068	2022-09-20 08:39:16.758661+00	2022-09-20 08:39:16.75869+00	1	\N	\N	f	\N
329	CUSTOMER	customer	Four Seasons Hotels and Resorts	14069	2022-09-20 08:39:16.758747+00	2022-09-20 08:39:16.758776+00	1	\N	\N	f	\N
330	CUSTOMER	customer	Freedom Mobile	14070	2022-09-20 08:39:16.758833+00	2022-09-20 08:39:16.758862+00	1	\N	\N	f	\N
331	CUSTOMER	customer	Riffwire	15001	2022-09-20 08:39:16.758918+00	2022-09-20 08:39:16.758947+00	1	\N	\N	f	\N
332	CUSTOMER	customer	Zoozzy	15002	2022-09-20 08:39:16.759003+00	2022-09-20 08:39:16.759032+00	1	\N	\N	f	\N
333	CUSTOMER	customer	Linkbuzz	15003	2022-09-20 08:39:16.759166+00	2022-09-20 08:39:16.759642+00	1	\N	\N	f	\N
334	CUSTOMER	customer	Brainlounge	15004	2022-09-20 08:39:16.759806+00	2022-09-20 08:39:16.759914+00	1	\N	\N	f	\N
335	CUSTOMER	customer	Pixonyx	15005	2022-09-20 08:39:16.760043+00	2022-09-20 08:39:16.760769+00	1	\N	\N	f	\N
336	CUSTOMER	customer	Bubblebox	15006	2022-09-20 08:39:16.761107+00	2022-09-20 08:39:16.761461+00	1	\N	\N	f	\N
337	CUSTOMER	customer	Yodel	15007	2022-09-20 08:39:16.763119+00	2022-09-20 08:39:16.763608+00	1	\N	\N	f	\N
338	CUSTOMER	customer	Trunyx	15008	2022-09-20 08:39:16.763818+00	2022-09-20 08:39:16.763887+00	1	\N	\N	f	\N
339	CUSTOMER	customer	Aimbu	15009	2022-09-20 08:39:16.764021+00	2022-09-20 08:39:16.764074+00	1	\N	\N	f	\N
340	CUSTOMER	customer	Yata	15010	2022-09-20 08:39:16.764203+00	2022-09-20 08:39:16.76437+00	1	\N	\N	f	\N
341	CUSTOMER	customer	Voonix	15011	2022-09-20 08:39:16.764496+00	2022-09-20 08:39:16.764544+00	1	\N	\N	f	\N
342	CUSTOMER	customer	Leexo	15012	2022-09-20 08:39:16.764653+00	2022-09-20 08:39:16.765674+00	1	\N	\N	f	\N
343	CUSTOMER	customer	Bubblemix	15013	2022-09-20 08:39:16.765758+00	2022-09-20 08:39:16.765792+00	1	\N	\N	f	\N
344	CUSTOMER	customer	Devbug	15014	2022-09-20 08:39:16.765856+00	2022-09-20 08:39:16.765879+00	1	\N	\N	f	\N
345	CUSTOMER	customer	Jazzy	15015	2022-09-20 08:39:16.765943+00	2022-09-20 08:39:16.765972+00	1	\N	\N	f	\N
346	CUSTOMER	customer	Voolith	15016	2022-09-20 08:39:16.766033+00	2022-09-20 08:39:16.766063+00	1	\N	\N	f	\N
347	CUSTOMER	customer	Skinte	15017	2022-09-20 08:39:16.766123+00	2022-09-20 08:39:16.766152+00	1	\N	\N	f	\N
348	CUSTOMER	customer	Izio	15018	2022-09-20 08:39:16.766211+00	2022-09-20 08:39:16.76624+00	1	\N	\N	f	\N
349	CUSTOMER	customer	Trudeo	15019	2022-09-20 08:39:16.766299+00	2022-09-20 08:39:16.766328+00	1	\N	\N	f	\N
350	CUSTOMER	customer	Jabberstorm	15020	2022-09-20 08:39:16.766386+00	2022-09-20 08:39:16.766415+00	1	\N	\N	f	\N
351	CUSTOMER	customer	Topicstorm	15021	2022-09-20 08:39:16.766473+00	2022-09-20 08:39:16.766502+00	1	\N	\N	f	\N
352	CUSTOMER	customer	Npath	15022	2022-09-20 08:39:16.766559+00	2022-09-20 08:39:16.766588+00	1	\N	\N	f	\N
353	CUSTOMER	customer	Photojam	15023	2022-09-20 08:39:16.766645+00	2022-09-20 08:39:16.766674+00	1	\N	\N	f	\N
354	CUSTOMER	customer	Twitterbeat	15024	2022-09-20 08:39:16.766731+00	2022-09-20 08:39:16.766761+00	1	\N	\N	f	\N
355	CUSTOMER	customer	Feednation	15025	2022-09-20 08:39:16.766817+00	2022-09-20 08:39:16.766846+00	1	\N	\N	f	\N
356	CUSTOMER	customer	Eadel	15026	2022-09-20 08:39:16.766904+00	2022-09-20 08:39:16.766933+00	1	\N	\N	f	\N
357	CUSTOMER	customer	Zoombeat	15027	2022-09-20 08:39:16.766989+00	2022-09-20 08:39:16.767018+00	1	\N	\N	f	\N
358	CUSTOMER	customer	Wikibox	15028	2022-09-20 08:39:16.767075+00	2022-09-20 08:39:16.767104+00	1	\N	\N	f	\N
359	CUSTOMER	customer	Edgeblab	15029	2022-09-20 08:39:16.767161+00	2022-09-20 08:39:16.76719+00	1	\N	\N	f	\N
360	CUSTOMER	customer	Kwilith	15030	2022-09-20 08:39:16.767247+00	2022-09-20 08:39:16.767276+00	1	\N	\N	f	\N
361	CUSTOMER	customer	Feedspan	15031	2022-09-20 08:39:16.767333+00	2022-09-20 08:39:16.767362+00	1	\N	\N	f	\N
362	CUSTOMER	customer	Flashdog	15032	2022-09-20 08:39:16.767418+00	2022-09-20 08:39:16.767447+00	1	\N	\N	f	\N
363	CUSTOMER	customer	Myworks	15033	2022-09-20 08:39:16.803897+00	2022-09-20 08:39:16.803977+00	1	\N	\N	f	\N
364	CUSTOMER	customer	Dynabox	15034	2022-09-20 08:39:16.804225+00	2022-09-20 08:39:16.804593+00	1	\N	\N	f	\N
365	CUSTOMER	customer	Browsebug	15035	2022-09-20 08:39:16.807804+00	2022-09-20 08:39:16.808172+00	1	\N	\N	f	\N
366	CUSTOMER	customer	Topiczoom	15036	2022-09-20 08:39:16.808769+00	2022-09-20 08:39:16.808811+00	1	\N	\N	f	\N
367	CUSTOMER	customer	Yombu	15037	2022-09-20 08:39:16.808886+00	2022-09-20 08:39:16.808913+00	1	\N	\N	f	\N
368	CUSTOMER	customer	Twitterbeat	15038	2022-09-20 08:39:16.80897+00	2022-09-20 08:39:16.809001+00	1	\N	\N	f	\N
369	CUSTOMER	customer	Divavu	15039	2022-09-20 08:39:16.809062+00	2022-09-20 08:39:16.809092+00	1	\N	\N	f	\N
370	CUSTOMER	customer	Quimm	15040	2022-09-20 08:39:16.809153+00	2022-09-20 08:39:16.809182+00	1	\N	\N	f	\N
371	CUSTOMER	customer	Miboo	15041	2022-09-20 08:39:16.809242+00	2022-09-20 08:39:16.809271+00	1	\N	\N	f	\N
372	CUSTOMER	customer	Feednation	15042	2022-09-20 08:39:16.80933+00	2022-09-20 08:39:16.809356+00	1	\N	\N	f	\N
373	CUSTOMER	customer	Trilith	15043	2022-09-20 08:39:16.809405+00	2022-09-20 08:39:16.809435+00	1	\N	\N	f	\N
374	CUSTOMER	customer	Photofeed	15044	2022-09-20 08:39:16.809493+00	2022-09-20 08:39:16.809522+00	1	\N	\N	f	\N
375	CUSTOMER	customer	Avaveo	15045	2022-09-20 08:39:16.809579+00	2022-09-20 08:39:16.809608+00	1	\N	\N	f	\N
376	CUSTOMER	customer	Bluejam	15046	2022-09-20 08:39:16.809666+00	2022-09-20 08:39:16.809695+00	1	\N	\N	f	\N
377	CUSTOMER	customer	BlogXS	15047	2022-09-20 08:39:16.809753+00	2022-09-20 08:39:16.809782+00	1	\N	\N	f	\N
378	CUSTOMER	customer	Thoughtworks	15048	2022-09-20 08:39:16.80984+00	2022-09-20 08:39:16.809869+00	1	\N	\N	f	\N
379	CUSTOMER	customer	Aimbu	15049	2022-09-20 08:39:16.809927+00	2022-09-20 08:39:16.809948+00	1	\N	\N	f	\N
380	CUSTOMER	customer	Livetube	15050	2022-09-20 08:39:16.809997+00	2022-09-20 08:39:16.81002+00	1	\N	\N	f	\N
381	CUSTOMER	customer	Livefish	15051	2022-09-20 08:39:16.810069+00	2022-09-20 08:39:16.810099+00	1	\N	\N	f	\N
382	CUSTOMER	customer	Skimia	15052	2022-09-20 08:39:16.810156+00	2022-09-20 08:39:16.810185+00	1	\N	\N	f	\N
383	CUSTOMER	customer	Jabbertype	15053	2022-09-20 08:39:16.810242+00	2022-09-20 08:39:16.810285+00	1	\N	\N	f	\N
384	CUSTOMER	customer	Feednation	15054	2022-09-20 08:39:16.810343+00	2022-09-20 08:39:16.810373+00	1	\N	\N	f	\N
385	CUSTOMER	customer	Tanoodle	15055	2022-09-20 08:39:16.81043+00	2022-09-20 08:39:16.810459+00	1	\N	\N	f	\N
386	CUSTOMER	customer	Dabtype	15056	2022-09-20 08:39:16.810516+00	2022-09-20 08:39:16.810545+00	1	\N	\N	f	\N
387	CUSTOMER	customer	Mybuzz	15057	2022-09-20 08:39:16.810602+00	2022-09-20 08:39:16.810632+00	1	\N	\N	f	\N
388	CUSTOMER	customer	Youbridge	15058	2022-09-20 08:39:16.810689+00	2022-09-20 08:39:16.810718+00	1	\N	\N	f	\N
389	CUSTOMER	customer	Rhycero	15059	2022-09-20 08:39:16.810775+00	2022-09-20 08:39:16.810805+00	1	\N	\N	f	\N
390	CUSTOMER	customer	Feednation	15060	2022-09-20 08:39:16.810862+00	2022-09-20 08:39:16.810891+00	1	\N	\N	f	\N
391	CUSTOMER	customer	Dabtype	15061	2022-09-20 08:39:16.810948+00	2022-09-20 08:39:16.810978+00	1	\N	\N	f	\N
392	CUSTOMER	customer	Jaxnation	15062	2022-09-20 08:39:16.811036+00	2022-09-20 08:39:16.811065+00	1	\N	\N	f	\N
393	CUSTOMER	customer	Topicware	15063	2022-09-20 08:39:16.811122+00	2022-09-20 08:39:16.81115+00	1	\N	\N	f	\N
394	CUSTOMER	customer	Voomm	15064	2022-09-20 08:39:16.811207+00	2022-09-20 08:39:16.811236+00	1	\N	\N	f	\N
395	CUSTOMER	customer	Skivee	15065	2022-09-20 08:39:16.811293+00	2022-09-20 08:39:16.811322+00	1	\N	\N	f	\N
396	CUSTOMER	customer	Topdrive	15066	2022-09-20 08:39:16.811378+00	2022-09-20 08:39:16.811407+00	1	\N	\N	f	\N
397	CUSTOMER	customer	Dabvine	15067	2022-09-20 08:39:16.811464+00	2022-09-20 08:39:16.811494+00	1	\N	\N	f	\N
398	CUSTOMER	customer	Thoughtstorm	15068	2022-09-20 08:39:16.81155+00	2022-09-20 08:39:16.81158+00	1	\N	\N	f	\N
399	CUSTOMER	customer	Kazio	15069	2022-09-20 08:39:16.811637+00	2022-09-20 08:39:16.811666+00	1	\N	\N	f	\N
400	CUSTOMER	customer	ABB Grain	16001	2022-09-20 08:39:16.811723+00	2022-09-20 08:39:16.811752+00	1	\N	\N	f	\N
401	CUSTOMER	customer	ABC Learning	16002	2022-09-20 08:39:16.811808+00	2022-09-20 08:39:16.811838+00	1	\N	\N	f	\N
402	CUSTOMER	customer	Adam Internet	16003	2022-09-20 08:39:16.826808+00	2022-09-20 08:39:16.826879+00	1	\N	\N	f	\N
403	CUSTOMER	customer	Aerosonde Ltd	16004	2022-09-20 08:39:16.827006+00	2022-09-20 08:39:16.827042+00	1	\N	\N	f	\N
404	CUSTOMER	customer	Alinta Gas	16005	2022-09-20 08:39:16.827134+00	2022-09-20 08:39:16.827176+00	1	\N	\N	f	\N
405	CUSTOMER	customer	Allphones	16006	2022-09-20 08:39:16.827268+00	2022-09-20 08:39:16.827441+00	1	\N	\N	f	\N
406	CUSTOMER	customer	Alumina	16007	2022-09-20 08:39:16.827528+00	2022-09-20 08:39:16.827569+00	1	\N	\N	f	\N
407	CUSTOMER	customer	Amcor	16008	2022-09-20 08:39:16.827649+00	2022-09-20 08:39:16.827688+00	1	\N	\N	f	\N
408	CUSTOMER	customer	ANCA	16009	2022-09-20 08:39:16.836776+00	2022-09-20 08:39:16.836824+00	1	\N	\N	f	\N
409	CUSTOMER	customer	Angus and Robertson	16010	2022-09-20 08:39:16.836901+00	2022-09-20 08:39:16.836935+00	1	\N	\N	f	\N
410	CUSTOMER	customer	Ansell	16011	2022-09-20 08:39:16.837006+00	2022-09-20 08:39:16.837038+00	1	\N	\N	f	\N
411	CUSTOMER	customer	Appliances Online	16012	2022-09-20 08:39:16.837105+00	2022-09-20 08:39:16.837135+00	1	\N	\N	f	\N
412	CUSTOMER	customer	Aristocrat Leisure	16013	2022-09-20 08:39:16.837192+00	2022-09-20 08:39:16.837221+00	1	\N	\N	f	\N
413	CUSTOMER	customer	Arnott's Biscuits	16014	2022-09-20 08:39:16.851047+00	2022-09-20 08:39:16.851087+00	1	\N	\N	f	\N
414	CUSTOMER	customer	Arrow Research Corporation	16015	2022-09-20 08:39:16.851158+00	2022-09-20 08:39:16.851179+00	1	\N	\N	f	\N
415	CUSTOMER	customer	Atlassian	16016	2022-09-20 08:39:16.851249+00	2022-09-20 08:39:16.851269+00	1	\N	\N	f	\N
416	CUSTOMER	customer	Aussie Broadband	16017	2022-09-20 08:39:16.85131+00	2022-09-20 08:39:16.851322+00	1	\N	\N	f	\N
417	CUSTOMER	customer	Austal Ships	16018	2022-09-20 08:39:16.851363+00	2022-09-20 08:39:16.851384+00	1	\N	\N	f	\N
418	CUSTOMER	customer	Austereo	16019	2022-09-20 08:39:16.851434+00	2022-09-20 08:39:16.851455+00	1	\N	\N	f	\N
419	CUSTOMER	customer	Australia and New Zealand Banking Group (ANZ)	16020	2022-09-20 08:39:16.851506+00	2022-09-20 08:39:16.851528+00	1	\N	\N	f	\N
420	CUSTOMER	customer	Australian Agricultural Company	16021	2022-09-20 08:39:16.851946+00	2022-09-20 08:39:16.855802+00	1	\N	\N	f	\N
421	CUSTOMER	customer	Australian airExpress	16022	2022-09-20 08:39:16.855944+00	2022-09-20 08:39:16.85598+00	1	\N	\N	f	\N
422	CUSTOMER	customer	Australian Broadcasting Corporation	16023	2022-09-20 08:39:16.856114+00	2022-09-20 08:39:16.856173+00	1	\N	\N	f	\N
423	CUSTOMER	customer	Australian Defence Industries	16024	2022-09-20 08:39:16.856329+00	2022-09-20 08:39:16.856372+00	1	\N	\N	f	\N
424	CUSTOMER	customer	Australian Gas Light Company	16025	2022-09-20 08:39:16.856435+00	2022-09-20 08:39:16.856457+00	1	\N	\N	f	\N
425	CUSTOMER	customer	Australian Motor Industries (AMI)	16026	2022-09-20 08:39:16.856507+00	2022-09-20 08:39:16.856519+00	1	\N	\N	f	\N
426	CUSTOMER	customer	Australian Railroad Group	16027	2022-09-20 08:39:16.856559+00	2022-09-20 08:39:16.856579+00	1	\N	\N	f	\N
427	CUSTOMER	customer	Australian Securities Exchange	16028	2022-09-20 08:39:16.856632+00	2022-09-20 08:39:16.856652+00	1	\N	\N	f	\N
428	CUSTOMER	customer	Ausway	16029	2022-09-20 08:39:16.856702+00	2022-09-20 08:39:16.856722+00	1	\N	\N	f	\N
429	CUSTOMER	customer	AWB Limited	16030	2022-09-20 08:39:16.856763+00	2022-09-20 08:39:16.856774+00	1	\N	\N	f	\N
430	CUSTOMER	customer	BAE Systems Australia	16031	2022-09-20 08:39:16.856816+00	2022-09-20 08:39:16.856836+00	1	\N	\N	f	\N
431	CUSTOMER	customer	Bakers Delight	16032	2022-09-20 08:39:16.856888+00	2022-09-20 08:39:16.856907+00	1	\N	\N	f	\N
432	CUSTOMER	customer	Beaurepaires	16033	2022-09-20 08:39:16.856947+00	2022-09-20 08:39:16.856958+00	1	\N	\N	f	\N
433	CUSTOMER	customer	Becker Entertainment	16034	2022-09-20 08:39:16.856999+00	2022-09-20 08:39:16.85702+00	1	\N	\N	f	\N
434	CUSTOMER	customer	Billabong	16035	2022-09-20 08:39:16.857071+00	2022-09-20 08:39:16.85709+00	1	\N	\N	f	\N
435	CUSTOMER	customer	Bing Lee	16036	2022-09-20 08:39:16.85713+00	2022-09-20 08:39:16.857141+00	1	\N	\N	f	\N
436	CUSTOMER	customer	BlueScope	16037	2022-09-20 08:39:16.857181+00	2022-09-20 08:39:16.857202+00	1	\N	\N	f	\N
437	CUSTOMER	customer	Blundstone Footwear	16038	2022-09-20 08:39:16.857252+00	2022-09-20 08:39:16.857272+00	1	\N	\N	f	\N
438	CUSTOMER	customer	Boost Juice Bars	16039	2022-09-20 08:39:16.857324+00	2022-09-20 08:39:16.857345+00	1	\N	\N	f	\N
439	CUSTOMER	customer	Boral	16040	2022-09-20 08:39:16.857395+00	2022-09-20 08:39:16.857416+00	1	\N	\N	f	\N
440	CUSTOMER	customer	Brown Brothers Milawa Vineyard	16041	2022-09-20 08:39:16.857467+00	2022-09-20 08:39:16.857488+00	1	\N	\N	f	\N
441	CUSTOMER	customer	Bulla Dairy Foods	16042	2022-09-20 08:39:16.857539+00	2022-09-20 08:39:16.85755+00	1	\N	\N	f	\N
442	CUSTOMER	customer	Burns Philp	16043	2022-09-20 08:39:16.857591+00	2022-09-20 08:39:16.857612+00	1	\N	\N	f	\N
443	CUSTOMER	customer	Camperdown Dairy International	16044	2022-09-20 08:39:16.857661+00	2022-09-20 08:39:16.857672+00	1	\N	\N	f	\N
444	CUSTOMER	customer	CBH Group	16045	2022-09-20 08:39:16.857713+00	2022-09-20 08:39:16.857733+00	1	\N	\N	f	\N
445	CUSTOMER	customer	Cbus	16046	2022-09-20 08:39:16.857783+00	2022-09-20 08:39:16.857805+00	1	\N	\N	f	\N
446	CUSTOMER	customer	CHEP	16047	2022-09-20 08:39:16.857855+00	2022-09-20 08:39:16.857876+00	1	\N	\N	f	\N
447	CUSTOMER	customer	CIMIC Group	16048	2022-09-20 08:39:16.857926+00	2022-09-20 08:39:16.857947+00	1	\N	\N	f	\N
448	CUSTOMER	customer	CMV Group	16049	2022-09-20 08:39:16.857997+00	2022-09-20 08:39:16.858007+00	1	\N	\N	f	\N
449	CUSTOMER	customer	Coca-Cola Amatil	16050	2022-09-20 08:39:16.858049+00	2022-09-20 08:39:16.858069+00	1	\N	\N	f	\N
450	CUSTOMER	customer	Coles Group	16051	2022-09-20 08:39:16.858121+00	2022-09-20 08:39:16.858132+00	1	\N	\N	f	\N
451	CUSTOMER	customer	Commonwealth Bank	16052	2022-09-20 08:39:16.858172+00	2022-09-20 08:39:16.858192+00	1	\N	\N	f	\N
452	CUSTOMER	customer	Compass Resources	16053	2022-09-20 08:39:16.858243+00	2022-09-20 08:39:16.858264+00	1	\N	\N	f	\N
453	CUSTOMER	customer	Computershare	16054	2022-09-20 08:39:16.858316+00	2022-09-20 08:39:16.858337+00	1	\N	\N	f	\N
454	CUSTOMER	customer	Cotton On	16055	2022-09-20 08:39:16.858386+00	2022-09-20 08:39:16.858407+00	1	\N	\N	f	\N
455	CUSTOMER	customer	Country Energy	16056	2022-09-20 08:39:16.85846+00	2022-09-20 08:39:16.858481+00	1	\N	\N	f	\N
456	CUSTOMER	customer	Crossecom	16057	2022-09-20 08:39:16.858537+00	2022-09-20 08:39:16.858567+00	1	\N	\N	f	\N
457	CUSTOMER	customer	Crown Resorts	16058	2022-09-20 08:39:16.858623+00	2022-09-20 08:39:16.858647+00	1	\N	\N	f	\N
458	CUSTOMER	customer	CSL Limited	16059	2022-09-20 08:39:16.858687+00	2022-09-20 08:39:16.858707+00	1	\N	\N	f	\N
459	CUSTOMER	customer	CSR Limited	16060	2022-09-20 08:39:16.858764+00	2022-09-20 08:39:16.858793+00	1	\N	\N	f	\N
460	CUSTOMER	customer	David Jones Limited	16061	2022-09-20 08:39:16.85885+00	2022-09-20 08:39:16.858869+00	1	\N	\N	f	\N
461	CUSTOMER	customer	De Bortoli Wines	16062	2022-09-20 08:39:16.858918+00	2022-09-20 08:39:16.858945+00	1	\N	\N	f	\N
462	CUSTOMER	customer	Delta Electricity	16063	2022-09-20 08:39:16.858992+00	2022-09-20 08:39:16.859022+00	1	\N	\N	f	\N
463	CUSTOMER	customer	Dick Smith Electronics	16064	2022-09-20 08:39:16.884802+00	2022-09-20 08:39:16.884855+00	1	\N	\N	f	\N
464	CUSTOMER	customer	Dorf Clark Industries	16065	2022-09-20 08:39:16.884933+00	2022-09-20 08:39:16.884967+00	1	\N	\N	f	\N
465	CUSTOMER	customer	Downer Group	16066	2022-09-20 08:39:16.888374+00	2022-09-20 08:39:16.888418+00	1	\N	\N	f	\N
466	CUSTOMER	customer	Dymocks Booksellers	16067	2022-09-20 08:39:16.888488+00	2022-09-20 08:39:16.888517+00	1	\N	\N	f	\N
467	CUSTOMER	customer	Eagle Boys	16068	2022-09-20 08:39:16.888649+00	2022-09-20 08:39:16.888763+00	1	\N	\N	f	\N
468	CUSTOMER	customer	Elders Limited	16069	2022-09-20 08:39:16.888952+00	2022-09-20 08:39:16.888988+00	1	\N	\N	f	\N
469	CUSTOMER	customer	Elfin Cars	16070	2022-09-20 08:39:16.889383+00	2022-09-20 08:39:16.88942+00	1	\N	\N	f	\N
470	CUSTOMER	customer	Adcock Ingram	17001	2022-09-20 08:39:16.889482+00	2022-09-20 08:39:16.889511+00	1	\N	\N	f	\N
471	CUSTOMER	customer	Afrihost	17002	2022-09-20 08:39:16.889559+00	2022-09-20 08:39:16.889572+00	1	\N	\N	f	\N
472	CUSTOMER	customer	ACSA	17003	2022-09-20 08:39:16.889613+00	2022-09-20 08:39:16.889625+00	1	\N	\N	f	\N
473	CUSTOMER	customer	Anglo American	17004	2022-09-20 08:39:16.88967+00	2022-09-20 08:39:16.889696+00	1	\N	\N	f	\N
474	CUSTOMER	customer	Anglo American Platinum	17005	2022-09-20 08:39:16.88988+00	2022-09-20 08:39:16.889913+00	1	\N	\N	f	\N
475	CUSTOMER	customer	Aspen Pharmacare	17006	2022-09-20 08:39:16.890119+00	2022-09-20 08:39:16.890159+00	1	\N	\N	f	\N
476	CUSTOMER	customer	Automobile Association of South Africa	17007	2022-09-20 08:39:16.890228+00	2022-09-20 08:39:16.890252+00	1	\N	\N	f	\N
477	CUSTOMER	customer	ABSA Group	17008	2022-09-20 08:39:16.890297+00	2022-09-20 08:39:16.890319+00	1	\N	\N	f	\N
478	CUSTOMER	customer	Business Connexion Group	17009	2022-09-20 08:39:16.890886+00	2022-09-20 08:39:16.890928+00	1	\N	\N	f	\N
479	CUSTOMER	customer	Capitec Bank	17010	2022-09-20 08:39:16.891041+00	2022-09-20 08:39:16.891064+00	1	\N	\N	f	\N
480	CUSTOMER	customer	Cell C	17011	2022-09-20 08:39:16.891114+00	2022-09-20 08:39:16.891135+00	1	\N	\N	f	\N
481	CUSTOMER	customer	Checkers	17012	2022-09-20 08:39:16.891184+00	2022-09-20 08:39:16.891216+00	1	\N	\N	f	\N
482	CUSTOMER	customer	De Beers	17013	2022-09-20 08:39:16.891632+00	2022-09-20 08:39:16.891667+00	1	\N	\N	f	\N
483	CUSTOMER	customer	Defy Appliances	17014	2022-09-20 08:39:16.891726+00	2022-09-20 08:39:16.891746+00	1	\N	\N	f	\N
484	CUSTOMER	customer	De Haan's Bus and Coach	17015	2022-09-20 08:39:16.891794+00	2022-09-20 08:39:16.891819+00	1	\N	\N	f	\N
485	CUSTOMER	customer	Dimension Data	17016	2022-09-20 08:39:16.891867+00	2022-09-20 08:39:16.891897+00	1	\N	\N	f	\N
486	CUSTOMER	customer	e.tv	17017	2022-09-20 08:39:16.892083+00	2022-09-20 08:39:16.892117+00	1	\N	\N	f	\N
487	CUSTOMER	customer	Eskom	17018	2022-09-20 08:39:16.892167+00	2022-09-20 08:39:16.892189+00	1	\N	\N	f	\N
488	CUSTOMER	customer	Exxaro	17019	2022-09-20 08:39:16.892475+00	2022-09-20 08:39:16.892525+00	1	\N	\N	f	\N
489	CUSTOMER	customer	Food Lover's Market	17020	2022-09-20 08:39:16.892591+00	2022-09-20 08:39:16.892622+00	1	\N	\N	f	\N
490	CUSTOMER	customer	First National Bank	17021	2022-09-20 08:39:16.893014+00	2022-09-20 08:39:16.893052+00	1	\N	\N	f	\N
491	CUSTOMER	customer	First Rand	17022	2022-09-20 08:39:16.900738+00	2022-09-20 08:39:16.90078+00	1	\N	\N	f	\N
492	CUSTOMER	customer	FNB Connect	17023	2022-09-20 08:39:16.900881+00	2022-09-20 08:39:16.901+00	1	\N	\N	f	\N
493	CUSTOMER	customer	Gallo Record Company	17024	2022-09-20 08:39:16.901053+00	2022-09-20 08:39:16.901083+00	1	\N	\N	f	\N
494	CUSTOMER	customer	Gijima Group	17025	2022-09-20 08:39:16.901132+00	2022-09-20 08:39:16.901162+00	1	\N	\N	f	\N
495	CUSTOMER	customer	Gold Fields	17026	2022-09-20 08:39:16.903613+00	2022-09-20 08:39:16.903714+00	1	\N	\N	f	\N
496	CUSTOMER	customer	Golden Arrow Bus Services	17027	2022-09-20 08:39:16.903819+00	2022-09-20 08:39:16.903847+00	1	\N	\N	f	\N
497	CUSTOMER	customer	Harmony Gold	17028	2022-09-20 08:39:16.904059+00	2022-09-20 08:39:16.906924+00	1	\N	\N	f	\N
498	CUSTOMER	customer	Hollard Group	17029	2022-09-20 08:39:16.907043+00	2022-09-20 08:39:16.907066+00	1	\N	\N	f	\N
499	CUSTOMER	customer	Illovo Sugar	17030	2022-09-20 08:39:16.90712+00	2022-09-20 08:39:16.907151+00	1	\N	\N	f	\N
500	CUSTOMER	customer	Impala Platinum	17031	2022-09-20 08:39:16.910215+00	2022-09-20 08:39:16.910304+00	1	\N	\N	f	\N
501	CUSTOMER	customer	Junk Mail Digital Media	17032	2022-09-20 08:39:16.912248+00	2022-09-20 08:39:16.912309+00	1	\N	\N	f	\N
502	CUSTOMER	customer	Kumba Iron Ore	17033	2022-09-20 08:39:16.912769+00	2022-09-20 08:39:16.912818+00	1	\N	\N	f	\N
503	CUSTOMER	customer	Investec	17034	2022-09-20 08:39:16.912887+00	2022-09-20 08:39:16.912912+00	1	\N	\N	f	\N
504	CUSTOMER	customer	LIFE Healthcare Group	17035	2022-09-20 08:39:16.913722+00	2022-09-20 08:39:16.913767+00	1	\N	\N	f	\N
505	CUSTOMER	customer	Mathews and Associates Architects	17036	2022-09-20 08:39:16.913855+00	2022-09-20 08:39:16.913877+00	1	\N	\N	f	\N
506	CUSTOMER	customer	Mediclinic International	17037	2022-09-20 08:39:16.91394+00	2022-09-20 08:39:16.913965+00	1	\N	\N	f	\N
507	CUSTOMER	customer	M-Net	17038	2022-09-20 08:39:16.914594+00	2022-09-20 08:39:16.914628+00	1	\N	\N	f	\N
508	CUSTOMER	customer	Mr. Price Group Ltd.	17039	2022-09-20 08:39:16.914686+00	2022-09-20 08:39:16.914719+00	1	\N	\N	f	\N
509	CUSTOMER	customer	MTN Group	17040	2022-09-20 08:39:16.916233+00	2022-09-20 08:39:16.916281+00	1	\N	\N	f	\N
510	CUSTOMER	customer	MultiChoice	17041	2022-09-20 08:39:16.916353+00	2022-09-20 08:39:16.916378+00	1	\N	\N	f	\N
511	CUSTOMER	customer	MWEB	17042	2022-09-20 08:39:16.917845+00	2022-09-20 08:39:16.918238+00	1	\N	\N	f	\N
512	CUSTOMER	customer	Naspers	17043	2022-09-20 08:39:16.922395+00	2022-09-20 08:39:16.934138+00	1	\N	\N	f	\N
513	CUSTOMER	customer	Nedbank	17044	2022-09-20 08:39:17.003534+00	2022-09-20 08:39:17.003599+00	1	\N	\N	f	\N
514	CUSTOMER	customer	Neotel	17045	2022-09-20 08:39:17.003691+00	2022-09-20 08:39:17.003728+00	1	\N	\N	f	\N
515	CUSTOMER	customer	Netcare	17046	2022-09-20 08:39:17.004393+00	2022-09-20 08:39:17.004442+00	1	\N	\N	f	\N
516	CUSTOMER	customer	Old Mutual	17047	2022-09-20 08:39:17.004512+00	2022-09-20 08:39:17.004545+00	1	\N	\N	f	\N
517	CUSTOMER	customer	Pick 'n Pay	17048	2022-09-20 08:39:17.004645+00	2022-09-20 08:39:17.004705+00	1	\N	\N	f	\N
518	CUSTOMER	customer	Pioneer Foods	17049	2022-09-20 08:39:17.00482+00	2022-09-20 08:39:17.004878+00	1	\N	\N	f	\N
519	CUSTOMER	customer	PPC Ltd.	17050	2022-09-20 08:39:17.005003+00	2022-09-20 08:39:17.005041+00	1	\N	\N	f	\N
520	CUSTOMER	customer	Premier FMCG	17051	2022-09-20 08:39:17.005109+00	2022-09-20 08:39:17.005139+00	1	\N	\N	f	\N
521	CUSTOMER	customer	Primedia	17052	2022-09-20 08:39:17.005201+00	2022-09-20 08:39:17.005231+00	1	\N	\N	f	\N
522	CUSTOMER	customer	Primedia Broadcasting	17053	2022-09-20 08:39:17.005294+00	2022-09-20 08:39:17.005322+00	1	\N	\N	f	\N
523	CUSTOMER	customer	PUTCO	17054	2022-09-20 08:39:17.008055+00	2022-09-20 08:39:17.008336+00	1	\N	\N	f	\N
524	CUSTOMER	customer	RCL Foods	17055	2022-09-20 08:39:17.008563+00	2022-09-20 08:39:17.008625+00	1	\N	\N	f	\N
525	CUSTOMER	customer	Riovic	17056	2022-09-20 08:39:17.008755+00	2022-09-20 08:39:17.008816+00	1	\N	\N	f	\N
526	CUSTOMER	customer	Rovos Rail	17057	2022-09-20 08:39:17.008928+00	2022-09-20 08:39:17.008972+00	1	\N	\N	f	\N
527	CUSTOMER	customer	South African Broadcasting Corporation	17058	2022-09-20 08:39:17.009073+00	2022-09-20 08:39:17.009116+00	1	\N	\N	f	\N
528	CUSTOMER	customer	Sanlam	17059	2022-09-20 08:39:17.009211+00	2022-09-20 08:39:17.009253+00	1	\N	\N	f	\N
529	CUSTOMER	customer	Sasol	17060	2022-09-20 08:39:17.009346+00	2022-09-20 08:39:17.009388+00	1	\N	\N	f	\N
530	CUSTOMER	customer	Shoprite	17061	2022-09-20 08:39:17.009481+00	2022-09-20 08:39:17.009522+00	1	\N	\N	f	\N
531	CUSTOMER	customer	South African Breweries	17062	2022-09-20 08:39:17.009616+00	2022-09-20 08:39:17.009658+00	1	\N	\N	f	\N
532	CUSTOMER	customer	Standard Bank	17063	2022-09-20 08:39:17.009748+00	2022-09-20 08:39:17.00979+00	1	\N	\N	f	\N
533	CUSTOMER	customer	StarSat, South Africa	17064	2022-09-20 08:39:17.009889+00	2022-09-20 08:39:17.009933+00	1	\N	\N	f	\N
534	CUSTOMER	customer	Telkom	17065	2022-09-20 08:39:17.010298+00	2022-09-20 08:39:17.010501+00	1	\N	\N	f	\N
535	CUSTOMER	customer	Telkom Mobile	17066	2022-09-20 08:39:17.010923+00	2022-09-20 08:39:17.010961+00	1	\N	\N	f	\N
536	CUSTOMER	customer	Tiger Brands	17067	2022-09-20 08:39:17.011031+00	2022-09-20 08:39:17.011063+00	1	\N	\N	f	\N
537	CUSTOMER	customer	Times Media Group	17068	2022-09-20 08:39:17.011126+00	2022-09-20 08:39:17.011149+00	1	\N	\N	f	\N
538	CUSTOMER	customer	Tongaat Hulett	17069	2022-09-20 08:39:17.011202+00	2022-09-20 08:39:17.011224+00	1	\N	\N	f	\N
539	DEPARTMENT	department	Admin	300	2022-09-20 08:39:22.956173+00	2022-09-20 08:39:22.956223+00	1	\N	\N	f	\N
540	DEPARTMENT	department	Services	200	2022-09-20 08:39:22.956293+00	2022-09-20 08:39:22.95685+00	1	\N	\N	f	\N
541	DEPARTMENT	department	Sales	100	2022-09-20 08:39:22.957032+00	2022-09-20 08:39:22.957059+00	1	\N	\N	f	\N
542	DEPARTMENT	department	IT	500	2022-09-20 08:39:22.957108+00	2022-09-20 08:39:22.957124+00	1	\N	\N	f	\N
543	DEPARTMENT	department	Marketing	400	2022-09-20 08:39:22.957166+00	2022-09-20 08:39:22.957179+00	1	\N	\N	f	\N
544	TAX_DETAIL	Tax Detail	UK Import Services Zero Rate	UK Import Services Zero Rate	2022-09-20 08:39:27.787535+00	2022-09-20 08:39:27.787614+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
545	TAX_DETAIL	Tax Detail	UK Purchase Goods Exempt Rate	UK Purchase Goods Exempt Rate	2022-09-20 08:39:27.787775+00	2022-09-20 08:39:27.787815+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
546	TAX_DETAIL	Tax Detail	UK Purchase Goods Reduced Rate	UK Purchase Goods Reduced Rate	2022-09-20 08:39:27.787908+00	2022-09-20 08:39:27.787939+00	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
547	TAX_DETAIL	Tax Detail	UK Purchase Goods Standard Rate	UK Purchase Goods Standard Rate	2022-09-20 08:39:27.788018+00	2022-09-20 08:39:27.788048+00	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
548	TAX_DETAIL	Tax Detail	UK Purchase Goods Zero Rate	UK Purchase Goods Zero Rate	2022-09-20 08:39:27.788121+00	2022-09-20 08:39:27.788151+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
549	TAX_DETAIL	Tax Detail	UK Purchase in Reverse Charge Box 6 Exempt UK	UK Purchase in Reverse Charge Box 6 Exempt UK	2022-09-20 08:39:27.788223+00	2022-09-20 08:39:27.788253+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
550	TAX_DETAIL	Tax Detail	UK Purchase in Reverse Charge Box 6 Reduced Rate UK Input	UK Purchase in Reverse Charge Box 6 Reduced Rate UK Input	2022-09-20 08:39:27.788323+00	2022-09-20 08:39:27.788352+00	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
551	TAX_DETAIL	Tax Detail	UK Purchase in Reverse Charge Box 6 Standard Rate UK Input	UK Purchase in Reverse Charge Box 6 Standard Rate UK Input	2022-09-20 08:39:27.788561+00	2022-09-20 08:39:27.788594+00	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
552	TAX_DETAIL	Tax Detail	UK Purchase in Reverse Charge Box 6 Zero Rate UK	UK Purchase in Reverse Charge Box 6 Zero Rate UK	2022-09-20 08:39:27.788665+00	2022-09-20 08:39:27.788706+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
553	TAX_DETAIL	Tax Detail	UK Purchase Reverse Charge Reduced Rate Input	UK Purchase Reverse Charge Reduced Rate Input	2022-09-20 08:39:27.788817+00	2022-09-20 08:39:27.78886+00	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
554	TAX_DETAIL	Tax Detail	UK Purchase Reverse Charge Standard Rate Input	UK Purchase Reverse Charge Standard Rate Input	2022-09-20 08:39:27.788978+00	2022-09-20 08:39:27.789016+00	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
555	TAX_DETAIL	Tax Detail	UK Purchase Services Exempt Rate	UK Purchase Services Exempt Rate	2022-09-20 08:39:27.78909+00	2022-09-20 08:39:27.789119+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
556	TAX_DETAIL	Tax Detail	UK Purchase Services Reduced Rate	UK Purchase Services Reduced Rate	2022-09-20 08:39:27.789191+00	2022-09-20 08:39:27.789221+00	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
557	TAX_DETAIL	Tax Detail	UK Purchase Services Standard Rate	UK Purchase Services Standard Rate	2022-09-20 08:39:27.789309+00	2022-09-20 08:39:27.789503+00	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
558	TAX_DETAIL	Tax Detail	UK Purchase Services Zero Rate	UK Purchase Services Zero Rate	2022-09-20 08:39:27.789629+00	2022-09-20 08:39:27.789663+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
559	TAX_DETAIL	Tax Detail	EC Purchase Goods Exempt Rate	EC Purchase Goods Exempt Rate	2022-09-20 08:39:27.789739+00	2022-09-20 08:39:27.789769+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
560	TAX_DETAIL	Tax Detail	EC Purchase Goods Reduced Rate Input	EC Purchase Goods Reduced Rate Input	2022-09-20 08:39:27.789844+00	2022-09-20 08:39:27.789874+00	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
561	TAX_DETAIL	Tax Detail	EC Purchase Goods Standard Rate Input	EC Purchase Goods Standard Rate Input	2022-09-20 08:39:27.789946+00	2022-09-20 08:39:27.789976+00	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
562	TAX_DETAIL	Tax Detail	EC Purchase Goods Zero Rate	EC Purchase Goods Zero Rate	2022-09-20 08:39:27.790047+00	2022-09-20 08:39:27.790078+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
563	TAX_DETAIL	Tax Detail	EC Purchase Services Exempt Rate	EC Purchase Services Exempt Rate	2022-09-20 08:39:27.790187+00	2022-09-20 08:39:27.790379+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
564	TAX_DETAIL	Tax Detail	EC Purchase Services Reduced Rate Input	EC Purchase Services Reduced Rate Input	2022-09-20 08:39:27.790632+00	2022-09-20 08:39:27.790674+00	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
565	TAX_DETAIL	Tax Detail	EC Purchase Services Standard Rate Input	EC Purchase Services Standard Rate Input	2022-09-20 08:39:27.790758+00	2022-09-20 08:39:27.790788+00	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
566	TAX_DETAIL	Tax Detail	EC Purchase Services Zero Rate	EC Purchase Services Zero Rate	2022-09-20 08:39:27.790864+00	2022-09-20 08:39:27.790894+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
567	TAX_DETAIL	Tax Detail	UK Import Goods Exempt Rate	UK Import Goods Exempt Rate	2022-09-20 08:39:27.790967+00	2022-09-20 08:39:27.790997+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
568	TAX_DETAIL	Tax Detail	UK Import Goods Reduced Rate	UK Import Goods Reduced Rate	2022-09-20 08:39:27.79107+00	2022-09-20 08:39:27.7911+00	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
569	TAX_DETAIL	Tax Detail	UK Import Goods Standard Rate	UK Import Goods Standard Rate	2022-09-20 08:39:27.791197+00	2022-09-20 08:39:27.791243+00	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
570	TAX_DETAIL	Tax Detail	UK Import Goods Zero Rate	UK Import Goods Zero Rate	2022-09-20 08:39:27.791506+00	2022-09-20 08:39:27.791538+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
571	TAX_DETAIL	Tax Detail	UK Import Services Exempt Rate	UK Import Services Exempt Rate	2022-09-20 08:39:27.791612+00	2022-09-20 08:39:27.791642+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
572	TAX_DETAIL	Tax Detail	UK Import Services Reduced Rate	UK Import Services Reduced Rate	2022-09-20 08:39:27.791714+00	2022-09-20 08:39:27.791751+00	1	t	{"tax_rate": 5.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
573	TAX_DETAIL	Tax Detail	UK Import Services Standard Rate	UK Import Services Standard Rate	2022-09-20 08:39:27.791866+00	2022-09-20 08:39:27.79191+00	1	t	{"tax_rate": 20.0, "tax_solution_id": "United Kingdom - VAT"}	f	\N
574	TAX_DETAIL	Tax Detail	G18 Input Tax Credit Adjustment	G18 Input Tax Credit Adjustment	2022-09-20 08:39:27.792025+00	2022-09-20 08:39:27.792067+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f	\N
575	TAX_DETAIL	Tax Detail	G13 Capital Purchases for Input Tax Sales	G13 Capital Purchases for Input Tax Sales	2022-09-20 08:39:27.792179+00	2022-09-20 08:39:27.792222+00	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f	\N
576	TAX_DETAIL	Tax Detail	G13 GST Free Capital Purchases for Input Tax Sales	G13 GST Free Capital Purchases for Input Tax Sales	2022-09-20 08:39:27.792359+00	2022-09-20 08:39:27.792556+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f	\N
577	TAX_DETAIL	Tax Detail	G15 Capital Purchases for Private Use	G15 Capital Purchases for Private Use	2022-09-20 08:39:27.792689+00	2022-09-20 08:39:27.792734+00	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f	\N
578	TAX_DETAIL	Tax Detail	G15 GST Free Capital Purchases for Private Use	G15 GST Free Capital Purchases for Private Use	2022-09-20 08:39:27.792826+00	2022-09-20 08:39:27.792857+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f	\N
579	TAX_DETAIL	Tax Detail	G10 Capital Acquisition	G10 Capital Acquisition	2022-09-20 08:39:27.792933+00	2022-09-20 08:39:27.792963+00	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f	\N
580	TAX_DETAIL	Tax Detail	G14 GST Free Capital Purchases	G14 GST Free Capital Purchases	2022-09-20 08:39:27.793037+00	2022-09-20 08:39:27.793066+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f	\N
581	TAX_DETAIL	Tax Detail	G13 Purchases for Input Tax Sales	G13 Purchases for Input Tax Sales	2022-09-20 08:39:27.793138+00	2022-09-20 08:39:27.793167+00	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f	\N
582	TAX_DETAIL	Tax Detail	G13 GST Free Purchases for Input Tax Sales	G13 GST Free Purchases for Input Tax Sales	2022-09-20 08:39:27.793238+00	2022-09-20 08:39:27.793268+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f	\N
583	TAX_DETAIL	Tax Detail	1F Luxury Car Tax Refundable	1F Luxury Car Tax Refundable	2022-09-20 08:39:27.793576+00	2022-09-20 08:39:27.793659+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f	\N
584	TAX_DETAIL	Tax Detail	G10 Motor Vehicle Acquisition	G10 Motor Vehicle Acquisition	2022-09-20 08:39:27.793809+00	2022-09-20 08:39:27.793943+00	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f	\N
585	TAX_DETAIL	Tax Detail	G11 Other Acquisition	G11 Other Acquisition	2022-09-20 08:39:27.794101+00	2022-09-20 08:39:27.794146+00	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f	\N
586	TAX_DETAIL	Tax Detail	G14 GST Free Non-Capital Purchases	G14 GST Free Non-Capital Purchases	2022-09-20 08:39:27.794525+00	2022-09-20 08:39:27.794595+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f	\N
587	TAX_DETAIL	Tax Detail	G15 Purchases for Private Use	G15 Purchases for Private Use	2022-09-20 08:39:27.794727+00	2022-09-20 08:39:27.794871+00	1	t	{"tax_rate": 10.0, "tax_solution_id": "Australia - GST"}	f	\N
588	TAX_DETAIL	Tax Detail	G15 GST Free Purchases for Private Use	G15 GST Free Purchases for Private Use	2022-09-20 08:39:27.795077+00	2022-09-20 08:39:27.795117+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f	\N
589	TAX_DETAIL	Tax Detail	1D Wine Equalisation Tax Refundable	1D Wine Equalisation Tax Refundable	2022-09-20 08:39:27.795252+00	2022-09-20 08:39:27.795653+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f	\N
590	TAX_DETAIL	Tax Detail	W4 Withholding Tax	W4 Withholding Tax	2022-09-20 08:39:27.795831+00	2022-09-20 08:39:27.795874+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "Australia - GST"}	f	\N
591	TAX_DETAIL	Tax Detail	Standard Rate Input	Standard Rate Input	2022-09-20 08:39:27.796052+00	2022-09-20 08:39:27.79611+00	1	t	{"tax_rate": 15.0, "tax_solution_id": "South Africa - VAT"}	f	\N
592	TAX_DETAIL	Tax Detail	Standard Rate (Capital Goods) Input	Standard Rate (Capital Goods) Input	2022-09-20 08:39:27.796254+00	2022-09-20 08:39:27.796436+00	1	t	{"tax_rate": 15.0, "tax_solution_id": "South Africa - VAT"}	f	\N
593	TAX_DETAIL	Tax Detail	Change in Use Input	Change in Use Input	2022-09-20 08:39:27.796537+00	2022-09-20 08:39:27.796577+00	1	t	{"tax_rate": 15.0, "tax_solution_id": "South Africa - VAT"}	f	\N
594	TAX_DETAIL	Tax Detail	Capital Goods Imported	Capital Goods Imported	2022-09-20 08:39:27.807918+00	2022-09-20 08:39:27.807958+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "South Africa - VAT"}	f	\N
595	TAX_DETAIL	Tax Detail	Other Goods Imported (Not Capital Goods)	Other Goods Imported (Not Capital Goods)	2022-09-20 08:39:27.808026+00	2022-09-20 08:39:27.808055+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "South Africa - VAT"}	f	\N
596	TAX_DETAIL	Tax Detail	Other Output Tax Adjustments	Other Output Tax Adjustments	2022-09-20 08:39:27.80812+00	2022-09-20 08:39:27.808148+00	1	t	{"tax_rate": 100.0, "tax_solution_id": "South Africa - VAT"}	f	\N
597	TAX_DETAIL	Tax Detail	No Input VAT	No Input VAT	2022-09-20 08:39:27.808213+00	2022-09-20 08:39:27.808241+00	1	t	{"tax_rate": 0.0, "tax_solution_id": "South Africa - VAT"}	f	\N
598	PROJECT	project	Direct Mail Campaign	10064	2022-09-20 08:39:34.293442+00	2022-09-20 08:39:34.293484+00	1	t	{"customer_id": "10064", "customer_name": "Med dot"}	f	\N
599	PROJECT	project	Branding Follow Up	10063	2022-09-20 08:39:34.293557+00	2022-09-20 08:39:34.293588+00	1	t	{"customer_id": "10063", "customer_name": "Portore"}	f	\N
600	PROJECT	project	labhvam	10083	2022-09-20 08:39:34.293908+00	2022-09-20 08:39:34.293939+00	1	t	{"customer_id": "10005", "customer_name": "Nirvana"}	f	\N
601	PROJECT	project	Ecommerce Campaign	10062	2022-09-20 08:39:34.294006+00	2022-09-20 08:39:34.294034+00	1	t	{"customer_id": "10062", "customer_name": "Vertous"}	f	\N
602	PROJECT	project	Branding Analysis	10061	2022-09-20 08:39:34.294099+00	2022-09-20 08:39:34.294126+00	1	t	{"customer_id": "10061", "customer_name": "Avu"}	f	\N
603	PROJECT	project	Mobile App Redesign	10080	2022-09-20 08:39:34.29419+00	2022-09-20 08:39:34.294218+00	1	t	{"customer_id": null, "customer_name": null}	f	\N
604	PROJECT	project	Platform APIs	10081	2022-09-20 08:39:34.294281+00	2022-09-20 08:39:34.294308+00	1	t	{"customer_id": null, "customer_name": null}	f	\N
605	PROJECT	project	Fyle NetSuite Integration	10078	2022-09-20 08:39:34.294492+00	2022-09-20 08:39:34.294539+00	1	t	{"customer_id": null, "customer_name": null}	f	\N
606	PROJECT	project	Fyle Sage Intacct Integration	10077	2022-09-20 08:39:34.294678+00	2022-09-20 08:39:34.294726+00	1	t	{"customer_id": null, "customer_name": null}	f	\N
607	PROJECT	project	Support Taxes	10082	2022-09-20 08:39:34.294831+00	2022-09-20 08:39:34.294862+00	1	t	{"customer_id": null, "customer_name": null}	f	\N
608	PROJECT	project	T&M Project with Five Tasks	Template-TM	2022-09-20 08:39:34.294936+00	2022-09-20 08:39:34.294964+00	1	t	{"customer_id": null, "customer_name": null}	f	\N
609	PROJECT	project	Fixed Fee Project with Five Tasks	Template-FF	2022-09-20 08:39:34.295028+00	2022-09-20 08:39:34.295056+00	1	t	{"customer_id": null, "customer_name": null}	f	\N
610	PROJECT	project	General Overhead	10000	2022-09-20 08:39:34.295119+00	2022-09-20 08:39:34.295146+00	1	t	{"customer_id": null, "customer_name": null}	f	\N
611	PROJECT	project	General Overhead-Current	10025	2022-09-20 08:39:34.295209+00	2022-09-20 08:39:34.295237+00	1	t	{"customer_id": null, "customer_name": null}	f	\N
675	VENDOR	vendor	Entity V100	20100	2022-09-20 08:40:03.838814+00	2022-09-20 08:40:03.838847+00	1	\N	{"email": null}	f	\N
612	PROJECT	project	Fyle Engineering	10079	2022-09-20 08:39:34.2953+00	2022-09-20 08:39:34.295327+00	1	t	{"customer_id": null, "customer_name": null}	f	\N
613	PROJECT	project	Integrations	10076	2022-09-20 08:39:34.295505+00	2022-09-20 08:39:34.29553+00	1	t	{"customer_id": null, "customer_name": null}	f	\N
614	EXPENSE_PAYMENT_TYPE	expense payment type	Company Credit Card	1	2022-09-20 08:39:45.743113+00	2022-09-20 08:39:45.743385+00	1	\N	{"is_reimbursable": false}	f	\N
615	CLASS	class	Small Business	400	2022-09-20 08:39:48.468017+00	2022-09-20 08:39:48.468059+00	1	\N	\N	f	\N
616	CLASS	class	Midsize Business	500	2022-09-20 08:39:48.468115+00	2022-09-20 08:39:48.468143+00	1	\N	\N	f	\N
617	CLASS	class	Enterprise	600	2022-09-20 08:39:48.468196+00	2022-09-20 08:39:48.468223+00	1	\N	\N	f	\N
618	CLASS	class	Service Line 2	200	2022-09-20 08:39:48.468276+00	2022-09-20 08:39:48.468303+00	1	\N	\N	f	\N
619	CLASS	class	Service Line 1	100	2022-09-20 08:39:48.468356+00	2022-09-20 08:39:48.468383+00	1	\N	\N	f	\N
620	CLASS	class	Service Line 3	300	2022-09-20 08:39:48.468597+00	2022-09-20 08:39:48.468637+00	1	\N	\N	f	\N
621	CHARGE_CARD_NUMBER	Charge Card Account	Charge Card 1	Charge Card 1	2022-09-20 08:39:52.257834+00	2022-09-20 08:39:52.257879+00	1	\N	\N	f	\N
622	CHARGE_CARD_NUMBER	Charge Card Account	nilesh	nilesh	2022-09-20 08:39:52.257935+00	2022-09-20 08:39:52.25795+00	1	\N	\N	f	\N
623	CHARGE_CARD_NUMBER	Charge Card Account	nilesh2	nilesh2	2022-09-20 08:39:52.257988+00	2022-09-20 08:39:52.258009+00	1	\N	\N	f	\N
624	CHARGE_CARD_NUMBER	Charge Card Account	jojobubu	jojobubu	2022-09-20 08:39:52.258075+00	2022-09-20 08:39:52.258103+00	1	\N	\N	f	\N
625	CHARGE_CARD_NUMBER	Charge Card Account	creditcardsecondry	creditcardsecondry	2022-09-20 08:39:52.258156+00	2022-09-20 08:39:52.258184+00	1	\N	\N	f	\N
626	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 500_CHK	500_CHK	2022-09-20 08:40:00.017808+00	2022-09-20 08:40:00.018547+00	1	\N	\N	f	\N
627	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 400_CHK	400_CHK	2022-09-20 08:40:00.018865+00	2022-09-20 08:40:00.018968+00	1	\N	\N	f	\N
628	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 700_CHK	700_CHK	2022-09-20 08:40:00.019271+00	2022-09-20 08:40:00.019311+00	1	\N	\N	f	\N
629	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 100_CHK	100_CHK	2022-09-20 08:40:00.019399+00	2022-09-20 08:40:00.019442+00	1	\N	\N	f	\N
630	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 300_CHK	300_CHK	2022-09-20 08:40:00.019538+00	2022-09-20 08:40:00.019581+00	1	\N	\N	f	\N
631	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 200_CHK	200_CHK	2022-09-20 08:40:00.019678+00	2022-09-20 08:40:00.019728+00	1	\N	\N	f	\N
632	PAYMENT_ACCOUNT	Payment Account	Demo Bank - 600_CHK	600_CHK	2022-09-20 08:40:00.019836+00	2022-09-20 08:40:00.019888+00	1	\N	\N	f	\N
633	VENDOR	vendor	Vaishnavi Primary	Vaishnavi Primary	2022-09-20 08:40:03.828715+00	2022-09-20 08:40:03.828765+00	1	\N	{"email": "vaishnavi.mohan+primary@fyle.in"}	f	\N
634	VENDOR	vendor	VM	VM	2022-09-20 08:40:03.828973+00	2022-09-20 08:40:03.829002+00	1	\N	{"email": "vaishnavi.mohan@fyle.in"}	f	\N
635	VENDOR	vendor	Yash	Yash	2022-09-20 08:40:03.831136+00	2022-09-20 08:40:03.831205+00	1	\N	{"email": "ajain@fyle.in"}	f	\N
636	VENDOR	vendor	gokul	gokul	2022-09-20 08:40:03.83134+00	2022-09-20 08:40:03.831373+00	1	\N	{"email": "gokul.kathiresan@fyle.in"}	f	\N
637	VENDOR	vendor	Nilesh, Dhoni	Nilesh2 Dhoni	2022-09-20 08:40:03.831454+00	2022-09-20 08:40:03.831486+00	1	\N	{"email": "india2@vendor.com"}	f	\N
638	VENDOR	vendor	Sachin, Saran	Sachin Saran	2022-09-20 08:40:03.831567+00	2022-09-20 08:40:03.83159+00	1	\N	{"email": "user5@fyleforbill.je"}	f	\N
639	VENDOR	vendor	Victor Martinez	Victor Martinez	2022-09-20 08:40:03.831657+00	2022-09-20 08:40:03.831683+00	1	\N	{"email": "user6@fyleforbill.cct"}	f	\N
640	VENDOR	vendor	akavuluru	akavuluru	2022-09-20 08:40:03.831745+00	2022-09-20 08:40:03.831767+00	1	\N	{"email": "akavuluru@fyle-us.com"}	f	\N
641	VENDOR	vendor	Srav	Srav	2022-09-20 08:40:03.831837+00	2022-09-20 08:40:03.831867+00	1	\N	{"email": "sravan.kumar@fyle.in"}	f	\N
642	VENDOR	vendor	Chris Curtis	Chris Curtis	2022-09-20 08:40:03.831936+00	2022-09-20 08:40:03.831965+00	1	\N	{"email": "user5@fyleforbill.cct"}	f	\N
643	VENDOR	vendor	James Taylor	James Taylor	2022-09-20 08:40:03.832034+00	2022-09-20 08:40:03.832054+00	1	\N	{"email": "user7@fyleforbill.cct"}	f	\N
644	VENDOR	vendor	Matthew Estrada	Matthew Estrada	2022-09-20 08:40:03.832116+00	2022-09-20 08:40:03.832636+00	1	\N	{"email": "user10@fyleforbill.cct"}	f	\N
645	VENDOR	vendor	Samantha Washington	Samantha Washington	2022-09-20 08:40:03.833274+00	2022-09-20 08:40:03.833314+00	1	\N	{"email": "user4@fyleforbill.cct"}	f	\N
646	VENDOR	vendor	Ashwin from NetSuite	Ashwin from NetSuite	2022-09-20 08:40:03.833406+00	2022-09-20 08:40:03.833438+00	1	\N	{"email": "ashwin.t@fyle.in"}	f	\N
647	VENDOR	vendor	Justin Glass	Justin Glass	2022-09-20 08:40:03.833616+00	2022-09-20 08:40:03.834056+00	1	\N	{"email": "user9@fyleforbill.cct"}	f	\N
648	VENDOR	vendor	Brian Foster	Brian Foster	2022-09-20 08:40:03.834295+00	2022-09-20 08:40:03.834327+00	1	\N	{"email": "user2@fyleforbill.cct"}	f	\N
649	VENDOR	vendor	Jessica Lane	Jessica Lane	2022-09-20 08:40:03.834405+00	2022-09-20 08:40:03.83442+00	1	\N	{"email": "user8@fyleforbill.cct"}	f	\N
650	VENDOR	vendor	Natalie Pope	Natalie Pope	2022-09-20 08:40:03.83448+00	2022-09-20 08:40:03.83451+00	1	\N	{"email": "user3@fyleforbill.cct"}	f	\N
651	VENDOR	vendor	Kristofferson Consulting	20014	2022-09-20 08:40:03.834573+00	2022-09-20 08:40:03.834595+00	1	\N	{"email": null}	f	\N
652	VENDOR	vendor	HC Equipment Repair	20015	2022-09-20 08:40:03.834664+00	2022-09-20 08:40:03.834693+00	1	\N	{"email": null}	f	\N
653	VENDOR	vendor	Kaufman & Langer LLP	20013	2022-09-20 08:40:03.835117+00	2022-09-20 08:40:03.835242+00	1	\N	{"email": null}	f	\N
654	VENDOR	vendor	Global Properties Inc.	20002	2022-09-20 08:40:03.835515+00	2022-09-20 08:40:03.835549+00	1	\N	{"email": null}	f	\N
655	VENDOR	vendor	ADP	20003	2022-09-20 08:40:03.835803+00	2022-09-20 08:40:03.835829+00	1	\N	{"email": null}	f	\N
656	VENDOR	vendor	National Grid	20004	2022-09-20 08:40:03.835898+00	2022-09-20 08:40:03.835929+00	1	\N	{"email": null}	f	\N
657	VENDOR	vendor	Lenovo	20007	2022-09-20 08:40:03.835996+00	2022-09-20 08:40:03.836026+00	1	\N	{"email": null}	f	\N
658	VENDOR	vendor	State Bank	20011	2022-09-20 08:40:03.836083+00	2022-09-20 08:40:03.836104+00	1	\N	{"email": null}	f	\N
659	VENDOR	vendor	Linda Hicks	20021	2022-09-20 08:40:03.83617+00	2022-09-20 08:40:03.836199+00	1	\N	{"email": null}	f	\N
660	VENDOR	vendor	Lee Thomas	20022	2022-09-20 08:40:03.836345+00	2022-09-20 08:40:03.83637+00	1	\N	{"email": null}	f	\N
661	VENDOR	vendor	Singleton Brothers CPA	20012	2022-09-20 08:40:03.836434+00	2022-09-20 08:40:03.836455+00	1	\N	{"email": null}	f	\N
662	VENDOR	vendor	The Nonprofit Alliance	20017	2022-09-20 08:40:03.836778+00	2022-09-20 08:40:03.836847+00	1	\N	{"email": null}	f	\N
663	VENDOR	vendor	Massachusetts Department of Revenue	20001	2022-09-20 08:40:03.837024+00	2022-09-20 08:40:03.83706+00	1	\N	{"email": null}	f	\N
664	VENDOR	vendor	Entity V600	20600	2022-09-20 08:40:03.837241+00	2022-09-20 08:40:03.837454+00	1	\N	{"email": null}	f	\N
665	VENDOR	vendor	Entity V500	20500	2022-09-20 08:40:03.837664+00	2022-09-20 08:40:03.837735+00	1	\N	{"email": null}	f	\N
666	VENDOR	vendor	Entity V400	20400	2022-09-20 08:40:03.837834+00	2022-09-20 08:40:03.837861+00	1	\N	{"email": null}	f	\N
667	VENDOR	vendor	Entity V700	20700	2022-09-20 08:40:03.837931+00	2022-09-20 08:40:03.837956+00	1	\N	{"email": null}	f	\N
668	VENDOR	vendor	Worldwide Commercial	20008	2022-09-20 08:40:03.838019+00	2022-09-20 08:40:03.838208+00	1	\N	{"email": null}	f	\N
669	VENDOR	vendor	Citi Bank	20009	2022-09-20 08:40:03.838292+00	2022-09-20 08:40:03.838316+00	1	\N	{"email": null}	f	\N
670	VENDOR	vendor	River Glen Insurance	20018	2022-09-20 08:40:03.838377+00	2022-09-20 08:40:03.838407+00	1	\N	{"email": null}	f	\N
671	VENDOR	vendor	Hanson Learning Solutions	20019	2022-09-20 08:40:03.838485+00	2022-09-20 08:40:03.838504+00	1	\N	{"email": null}	f	\N
672	VENDOR	vendor	Neighborhood Printers	20020	2022-09-20 08:40:03.838562+00	2022-09-20 08:40:03.838595+00	1	\N	{"email": null}	f	\N
673	VENDOR	vendor	The Post Company	20016	2022-09-20 08:40:03.838648+00	2022-09-20 08:40:03.83867+00	1	\N	{"email": null}	f	\N
674	VENDOR	vendor	Green Team Waste Management	20010	2022-09-20 08:40:03.838742+00	2022-09-20 08:40:03.838761+00	1	\N	{"email": null}	f	\N
676	VENDOR	vendor	Entity V200	20200	2022-09-20 08:40:03.838922+00	2022-09-20 08:40:03.838961+00	1	\N	{"email": null}	f	\N
677	VENDOR	vendor	Entity V300	20300	2022-09-20 08:40:03.839181+00	2022-09-20 08:40:03.8392+00	1	\N	{"email": null}	f	\N
678	VENDOR	vendor	American Express	20006	2022-09-20 08:40:03.839245+00	2022-09-20 08:40:03.839266+00	1	\N	{"email": null}	f	\N
679	VENDOR	vendor	Canyon CPA	20061	2022-09-20 08:40:03.83934+00	2022-09-20 08:40:03.839377+00	1	\N	{"email": null}	f	\N
680	VENDOR	vendor	Paramount Consulting	20062	2022-09-20 08:40:03.839437+00	2022-09-20 08:40:03.839459+00	1	\N	{"email": null}	f	\N
681	VENDOR	vendor	Microns Consulting	20071	2022-09-20 08:40:03.839538+00	2022-09-20 08:40:03.839568+00	1	\N	{"email": null}	f	\N
682	VENDOR	vendor	Global Printing	20063	2022-09-20 08:40:03.839642+00	2022-09-20 08:40:03.839668+00	1	\N	{"email": null}	f	\N
683	VENDOR	vendor	Quick Post	20074	2022-09-20 08:40:03.852409+00	2022-09-20 08:40:03.852446+00	1	\N	{"email": null}	f	\N
684	VENDOR	vendor	Scribe Post	20064	2022-09-20 08:40:03.854483+00	2022-09-20 08:40:03.854613+00	1	\N	{"email": null}	f	\N
685	VENDOR	vendor	Vision Post	20073	2022-09-20 08:40:03.854935+00	2022-09-20 08:40:03.854985+00	1	\N	{"email": null}	f	\N
686	VENDOR	vendor	Magnolia CPA	20072	2022-09-20 08:40:03.855708+00	2022-09-20 08:40:03.85577+00	1	\N	{"email": null}	f	\N
687	VENDOR	vendor	Investor CPA	20051	2022-09-20 08:40:03.855906+00	2022-09-20 08:40:03.85596+00	1	\N	{"email": null}	f	\N
688	VENDOR	vendor	Quali Consultants	20052	2022-09-20 08:40:03.856136+00	2022-09-20 08:40:03.856411+00	1	\N	{"email": null}	f	\N
689	VENDOR	vendor	Prima Printing	20053	2022-09-20 08:40:03.857565+00	2022-09-20 08:40:03.857676+00	1	\N	{"email": null}	f	\N
690	VENDOR	vendor	Boardwalk Post	20054	2022-09-20 08:40:03.858867+00	2022-09-20 08:40:03.858918+00	1	\N	{"email": null}	f	\N
691	VENDOR	vendor	Consulting Grid	20041	2022-09-20 08:40:03.859006+00	2022-09-20 08:40:03.859037+00	1	\N	{"email": null}	f	\N
692	VENDOR	vendor	Cornerstone	20042	2022-09-20 08:40:03.859112+00	2022-09-20 08:40:03.859141+00	1	\N	{"email": null}	f	\N
693	VENDOR	vendor	Advisor Printing	20043	2022-09-20 08:40:03.859208+00	2022-09-20 08:40:03.859237+00	1	\N	{"email": null}	f	\N
694	VENDOR	vendor	Prosper Post	20044	2022-09-20 08:40:03.859304+00	2022-09-20 08:40:03.859333+00	1	\N	{"email": null}	f	\N
695	VENDOR	vendor	National Insurance	20005	2022-09-20 08:40:03.859401+00	2022-09-20 08:40:03.859433+00	1	\N	{"email": null}	f	\N
696	VENDOR	vendor	Joshua Wood	Joshua Wood	2022-09-20 08:40:03.859502+00	2022-09-20 08:40:03.859692+00	1	\N	{"email": "user1@fyleforbill.cct"}	f	\N
697	VENDOR	vendor	Theresa Brown	Theresa Brown	2022-09-20 08:40:03.859791+00	2022-09-20 08:40:03.859814+00	1	\N	{"email": "admin1@fyleforselectcfieldsns.in"}	f	\N
698	VENDOR	vendor	Credit Card Misc	Credit Card Misc	2022-09-20 08:40:03.859917+00	2022-09-20 08:40:03.859933+00	1	\N	{"email": null}	f	\N
699	VENDOR	vendor	Ashwin	Ashwin	2022-09-20 08:40:03.859986+00	2022-09-20 08:40:03.860016+00	1	\N	{"email": "ashwin.t@fyle.in"}	f	\N
700	EMPLOYEE	employee	Franco, Ryan	1005	2022-09-20 08:40:08.456834+00	2022-09-20 08:40:08.456891+00	1	\N	{"email": "ryan@demo.com", "full_name": "Franco, Ryan", "location_id": null, "department_id": "100"}	f	\N
701	EMPLOYEE	employee	Evans, Chelsea	1004	2022-09-20 08:40:08.45699+00	2022-09-20 08:40:08.457025+00	1	\N	{"email": "chelsea@demo.com", "full_name": "Evans, Chelsea", "location_id": null, "department_id": "200"}	f	\N
702	EMPLOYEE	employee	Klein, Tom	1001	2022-09-20 08:40:08.45711+00	2022-09-20 08:40:08.457141+00	1	\N	{"email": "tom@demo.com", "full_name": "Klein, Tom", "location_id": null, "department_id": "300"}	f	\N
703	EMPLOYEE	employee	Tesla, Nikki	1003	2022-09-20 08:40:08.457221+00	2022-09-20 08:40:08.457252+00	1	\N	{"email": "nikki@demo.com", "full_name": "Tesla, Nikki", "location_id": null, "department_id": "200"}	f	\N
704	EMPLOYEE	employee	Moloney, Mark	1007	2022-09-20 08:40:08.457328+00	2022-09-20 08:40:08.457359+00	1	\N	{"email": "mark@demo.com", "full_name": "Moloney, Mark", "location_id": null, "department_id": "400"}	f	\N
705	EMPLOYEE	employee	Collins, Mike	1026	2022-09-20 08:40:08.457433+00	2022-09-20 08:40:08.457462+00	1	\N	{"email": "mike@demo.com", "full_name": "Collins, Mike", "location_id": null, "department_id": null}	f	\N
706	EMPLOYEE	employee	Penny, Emma	1000	2022-09-20 08:40:08.457533+00	2022-09-20 08:40:08.457562+00	1	\N	{"email": "emma@demo.com", "full_name": "Penny, Emma", "location_id": null, "department_id": "300"}	f	\N
707	EMPLOYEE	employee	Joanna	Joanna	2022-09-20 08:40:08.457633+00	2022-09-20 08:40:08.457662+00	1	\N	{"email": "ashwin.t@fyle.in", "full_name": "Joanna", "location_id": null, "department_id": "300"}	f	\N
708	EMPLOYEE	employee	Labhvam Bhaiya	Labhvam Bhaiya	2022-09-20 08:40:08.457733+00	2022-09-20 08:40:08.457762+00	1	\N	{"email": "user4@fylefordashboard1.com", "full_name": "Labhvam Bhaiya", "location_id": null, "department_id": "300"}	f	\N
709	EMPLOYEE	employee	Brian Foster	Brian Foster	2022-09-20 08:40:08.457866+00	2022-09-20 08:40:08.457917+00	1	\N	{"email": "user2@fyleforfyle.cleanup", "full_name": "Brian Foster", "location_id": null, "department_id": "300"}	f	\N
710	EMPLOYEE	employee	Chris Curtis	Chris Curtis	2022-09-20 08:40:08.458307+00	2022-09-20 08:40:08.458332+00	1	\N	{"email": "user5@fyleforfyle.cleanup", "full_name": "Chris Curtis", "location_id": null, "department_id": "300"}	f	\N
711	EMPLOYEE	employee	Real OG	Real OG	2022-09-20 08:40:08.458396+00	2022-09-20 08:40:08.458427+00	1	\N	{"email": "user7@fyleforfyle.cleanup", "full_name": "Real OG", "location_id": null, "department_id": "300"}	f	\N
712	EMPLOYEE	employee	Gale, Brittney	1074	2022-09-20 08:40:08.458499+00	2022-09-20 08:40:08.458529+00	1	\N	{"email": null, "full_name": "Gale, Brittney", "location_id": null, "department_id": "200"}	f	\N
713	EMPLOYEE	employee	Darwin, Chuck	1002	2022-09-20 08:40:08.4586+00	2022-09-20 08:40:08.45863+00	1	\N	{"email": "chuck@demo.com", "full_name": "Darwin, Chuck", "location_id": null, "department_id": "300"}	f	\N
714	EMPLOYEE	employee	Designer	1023	2022-09-20 08:40:08.458699+00	2022-09-20 08:40:08.458728+00	1	\N	{"email": null, "full_name": "Designer", "location_id": null, "department_id": null}	f	\N
715	EMPLOYEE	employee	Rhodes, Giorgia	1062	2022-09-20 08:40:08.458798+00	2022-09-20 08:40:08.458828+00	1	\N	{"email": null, "full_name": "Rhodes, Giorgia", "location_id": "600", "department_id": "500"}	f	\N
716	EMPLOYEE	employee	Rayner, Abigail	1052	2022-09-20 08:40:08.458897+00	2022-09-20 08:40:08.458926+00	1	\N	{"email": null, "full_name": "Rayner, Abigail", "location_id": null, "department_id": "200"}	f	\N
717	EMPLOYEE	employee	Donovan, Simra	1044	2022-09-20 08:40:08.458996+00	2022-09-20 08:40:08.459038+00	1	\N	{"email": null, "full_name": "Donovan, Simra", "location_id": null, "department_id": "400"}	f	\N
718	EMPLOYEE	employee	Searle, Lola	1054	2022-09-20 08:40:08.459159+00	2022-09-20 08:40:08.459203+00	1	\N	{"email": null, "full_name": "Searle, Lola", "location_id": null, "department_id": "300"}	f	\N
719	EMPLOYEE	employee	Hodges, Jerome	1064	2022-09-20 08:40:08.45932+00	2022-09-20 08:40:08.459367+00	1	\N	{"email": null, "full_name": "Hodges, Jerome", "location_id": "600", "department_id": "300"}	f	\N
720	EMPLOYEE	employee	Draper, Shelbie	1071	2022-09-20 08:40:08.45949+00	2022-09-20 08:40:08.459539+00	1	\N	{"email": null, "full_name": "Draper, Shelbie", "location_id": null, "department_id": "200"}	f	\N
721	EMPLOYEE	employee	Barker, Brendan	1072	2022-09-20 08:40:08.459661+00	2022-09-20 08:40:08.459704+00	1	\N	{"email": null, "full_name": "Barker, Brendan", "location_id": null, "department_id": "200"}	f	\N
722	EMPLOYEE	employee	Meadows, Tommy	1061	2022-09-20 08:40:08.459939+00	2022-09-20 08:40:08.459999+00	1	\N	{"email": null, "full_name": "Meadows, Tommy", "location_id": "600", "department_id": "200"}	f	\N
723	EMPLOYEE	employee	Regan, Bruce	1063	2022-09-20 08:40:08.460132+00	2022-09-20 08:40:08.460176+00	1	\N	{"email": null, "full_name": "Regan, Bruce", "location_id": "600", "department_id": "100"}	f	\N
724	EMPLOYEE	employee	Preece, Ewan	1073	2022-09-20 08:40:08.460294+00	2022-09-20 08:40:08.460339+00	1	\N	{"email": null, "full_name": "Preece, Ewan", "location_id": null, "department_id": "300"}	f	\N
725	EMPLOYEE	employee	Singh, Sanjay	1011	2022-09-20 08:40:08.467702+00	2022-09-20 08:40:08.467875+00	1	\N	{"email": "sanjay@demo.com", "full_name": "Singh, Sanjay", "location_id": null, "department_id": "100"}	f	\N
726	EMPLOYEE	employee	Monaghan, Toyah	1043	2022-09-20 08:40:08.468576+00	2022-09-20 08:40:08.468797+00	1	\N	{"email": null, "full_name": "Monaghan, Toyah", "location_id": null, "department_id": "300"}	f	\N
727	EMPLOYEE	employee	Saunders, Jill	1018	2022-09-20 08:40:08.469652+00	2022-09-20 08:40:08.469702+00	1	\N	{"email": "jill@demo.com", "full_name": "Saunders, Jill", "location_id": null, "department_id": "400"}	f	\N
728	EMPLOYEE	employee	Director	1022	2022-09-20 08:40:08.469829+00	2022-09-20 08:40:08.469877+00	1	\N	{"email": null, "full_name": "Director", "location_id": null, "department_id": null}	f	\N
729	EMPLOYEE	employee	Developer	1024	2022-09-20 08:40:08.470491+00	2022-09-20 08:40:08.47072+00	1	\N	{"email": null, "full_name": "Developer", "location_id": null, "department_id": null}	f	\N
730	EMPLOYEE	employee	Consultant	1025	2022-09-20 08:40:08.472746+00	2022-09-20 08:40:08.472887+00	1	\N	{"email": null, "full_name": "Consultant", "location_id": null, "department_id": null}	f	\N
731	EMPLOYEE	employee	Project Manager	1021	2022-09-20 08:40:08.473093+00	2022-09-20 08:40:08.47312+00	1	\N	{"email": null, "full_name": "Project Manager", "location_id": null, "department_id": null}	f	\N
732	EMPLOYEE	employee	Ponce, Gail	1042	2022-09-20 08:40:08.47329+00	2022-09-20 08:40:08.473419+00	1	\N	{"email": null, "full_name": "Ponce, Gail", "location_id": null, "department_id": "100"}	f	\N
733	EMPLOYEE	employee	Torres, Dario	1041	2022-09-20 08:40:08.473496+00	2022-09-20 08:40:08.47352+00	1	\N	{"email": null, "full_name": "Torres, Dario", "location_id": null, "department_id": "300"}	f	\N
734	EMPLOYEE	employee	Haines, Annika	1051	2022-09-20 08:40:08.473599+00	2022-09-20 08:40:08.474286+00	1	\N	{"email": null, "full_name": "Haines, Annika", "location_id": null, "department_id": "200"}	f	\N
735	EMPLOYEE	employee	Medrano, Jenson	1053	2022-09-20 08:40:08.480723+00	2022-09-20 08:40:08.481196+00	1	\N	{"email": null, "full_name": "Medrano, Jenson", "location_id": null, "department_id": "200"}	f	\N
736	EMPLOYEE	employee	Chen, Kathryn	1006	2022-09-20 08:40:08.481481+00	2022-09-20 08:40:08.481539+00	1	\N	{"email": "kathryn@demo.com", "full_name": "Chen, Kathryn", "location_id": null, "department_id": "100"}	f	\N
737	EMPLOYEE	employee	Hoffman, Lisa	1008	2022-09-20 08:40:08.48166+00	2022-09-20 08:40:08.481694+00	1	\N	{"email": "lisa@demo.com", "full_name": "Hoffman, Lisa", "location_id": null, "department_id": "500"}	f	\N
738	EMPLOYEE	employee	Peters, Derek	1009	2022-09-20 08:40:08.481785+00	2022-09-20 08:40:08.481816+00	1	\N	{"email": "derek@demo.com", "full_name": "Peters, Derek", "location_id": null, "department_id": "200"}	f	\N
739	EMPLOYEE	employee	Wallace, Amy	1010	2022-09-20 08:40:08.481917+00	2022-09-20 08:40:08.481963+00	1	\N	{"email": "amy@demo.com", "full_name": "Wallace, Amy", "location_id": null, "department_id": "100"}	f	\N
740	EMPLOYEE	employee	King, Kristin	1012	2022-09-20 08:40:08.482174+00	2022-09-20 08:40:08.482206+00	1	\N	{"email": "kristin@demo.com", "full_name": "King, Kristin", "location_id": null, "department_id": "100"}	f	\N
741	EMPLOYEE	employee	Lee, Max	1013	2022-09-20 08:40:08.482317+00	2022-09-20 08:40:08.482339+00	1	\N	{"email": "max@demo.com", "full_name": "Lee, Max", "location_id": null, "department_id": "200"}	f	\N
742	EMPLOYEE	employee	Farley, Nicole	1014	2022-09-20 08:40:08.482407+00	2022-09-20 08:40:08.482448+00	1	\N	{"email": "nicole@demo.com", "full_name": "Farley, Nicole", "location_id": null, "department_id": "400"}	f	\N
743	EMPLOYEE	employee	Reyes, Christian	1015	2022-09-20 08:40:08.48254+00	2022-09-20 08:40:08.48257+00	1	\N	{"email": "christian@demo.com", "full_name": "Reyes, Christian", "location_id": null, "department_id": "500"}	f	\N
744	EMPLOYEE	employee	Chang, Andrew	1016	2022-09-20 08:40:08.482635+00	2022-09-20 08:40:08.482664+00	1	\N	{"email": "andrew@demo.com", "full_name": "Chang, Andrew", "location_id": null, "department_id": "200"}	f	\N
745	EMPLOYEE	employee	Gupta, Chandra	1017	2022-09-20 08:40:08.482743+00	2022-09-20 08:40:08.482774+00	1	\N	{"email": "chandra@demo.com", "full_name": "Gupta, Chandra", "location_id": null, "department_id": "400"}	f	\N
746	EMPLOYEE	employee	Hicks, Linda	1019	2022-09-20 08:40:08.482913+00	2022-09-20 08:40:08.48295+00	1	\N	{"email": "linda@demo.com", "full_name": "Hicks, Linda", "location_id": null, "department_id": "500"}	f	\N
747	EMPLOYEE	employee	Lee, Thomas	1020	2022-09-20 08:40:08.483222+00	2022-09-20 08:40:08.48326+00	1	\N	{"email": "thomas@demo.com", "full_name": "Lee, Thomas", "location_id": null, "department_id": "100"}	f	\N
748	EMPLOYEE	employee	Ryan Gallagher	Ryan Gallagher	2022-09-20 08:40:08.483351+00	2022-09-20 08:40:08.483391+00	1	\N	{"email": "approver1@fylefordashboard2.com", "full_name": "Ryan Gallagher", "location_id": "600", "department_id": "300"}	f	\N
749	EMPLOYEE	employee	Joshua Wood	Joshua Wood	2022-09-20 08:40:08.483463+00	2022-09-20 08:40:08.483487+00	1	\N	{"email": "user1@fylefordashboard2.com", "full_name": "Joshua Wood", "location_id": "600", "department_id": "300"}	f	\N
750	EMPLOYEE	employee	Matthew Estrada	Matthew Estrada	2022-09-20 08:40:08.50909+00	2022-09-20 08:40:08.509257+00	1	\N	{"email": "user10@fylefordashboard2.com", "full_name": "Matthew Estrada", "location_id": "600", "department_id": "300"}	f	\N
751	EMPLOYEE	employee	Natalie Pope	Natalie Pope	2022-09-20 08:40:08.509332+00	2022-09-20 08:40:08.509362+00	1	\N	{"email": "user3@fylefordashboard2.com", "full_name": "Natalie Pope", "location_id": "600", "department_id": "300"}	f	\N
752	EMPLOYEE	employee	Harman	1100	2022-09-20 08:40:08.50943+00	2022-09-20 08:40:08.509459+00	1	\N	{"email": "expensify@thatharmansingh.com", "full_name": "Harman", "location_id": "600", "department_id": null}	f	\N
753	EMPLOYEE	employee	Theresa Brown	Theresa Brown	2022-09-20 08:40:08.509526+00	2022-09-20 08:40:08.509555+00	1	\N	{"email": "admin1@fyleforfyle.cleanup", "full_name": "Theresa Brown", "location_id": null, "department_id": "300"}	f	\N
754	EMPLOYEE	employee	uchicha, itachi	1101	2022-09-20 08:40:08.509622+00	2022-09-20 08:40:08.509651+00	1	\N	{"email": null, "full_name": "uchicha, itachi", "location_id": "600", "department_id": null}	f	\N
933	ITEM	item	Billable Expenses	1004	2022-09-20 08:40:22.463786+00	2022-09-20 08:40:22.463827+00	1	\N	\N	f	\N
934	ITEM	item	Subcontractor Expenses	1005	2022-09-20 08:40:22.463883+00	2022-09-20 08:40:22.463911+00	1	\N	\N	f	\N
935	ITEM	item	Project Fee	1003	2022-09-20 08:40:22.463963+00	2022-09-20 08:40:22.46399+00	1	\N	\N	f	\N
936	ITEM	item	Service 1	1001	2022-09-20 08:40:22.464043+00	2022-09-20 08:40:22.46407+00	1	\N	\N	f	\N
937	ITEM	item	Service 2	1002	2022-09-20 08:40:22.464123+00	2022-09-20 08:40:22.464162+00	1	\N	\N	f	\N
938	ITEM	item	Cube	1012	2022-09-20 08:40:22.464438+00	2022-09-20 08:40:22.464576+00	1	\N	\N	f	\N
939	ITEM	item	This is added by L	321	2022-09-20 08:40:22.464713+00	2022-09-20 08:40:22.464745+00	1	\N	\N	f	\N
940	ITEM	item	New item to be added	1011	2022-09-20 08:40:22.464804+00	2022-09-20 08:40:22.464833+00	1	\N	\N	f	\N
941	TEAM	team	CCC	10003	2022-09-20 08:40:27.76449+00	2022-09-20 08:40:27.764531+00	1	\N	\N	f	\N
942	TEAM	team	Integrations	10002	2022-09-20 08:40:27.764587+00	2022-09-20 08:40:27.764615+00	1	\N	\N	f	\N
943	VENDOR	vendor	test Sharma	test Sharma	2022-09-29 12:09:25.990678+00	2022-09-29 12:09:25.99074+00	1	\N	{"email": "test@fyle.in"}	f	\N
755	ACCOUNT	account	Patents & Licenses	16200	2022-09-20 08:40:13.410332+00	2022-09-20 08:40:13.410376+00	1	t	{"account_type": "balancesheet"}	f	\N
756	ACCOUNT	account	Bank Charges	60600	2022-09-20 08:40:13.410441+00	2022-09-20 08:40:13.41047+00	1	t	{"account_type": "incomestatement"}	f	\N
757	ACCOUNT	account	COGS - Sales	50100	2022-09-20 08:40:13.410527+00	2022-09-20 08:40:13.410555+00	1	t	{"account_type": "incomestatement"}	f	\N
758	ACCOUNT	account	Employee Benefits	60110	2022-09-20 08:40:13.410612+00	2022-09-20 08:40:13.41064+00	1	t	{"account_type": "incomestatement"}	f	\N
759	ACCOUNT	account	Commission	60120	2022-09-20 08:40:13.410695+00	2022-09-20 08:40:13.410723+00	1	t	{"account_type": "incomestatement"}	f	\N
760	ACCOUNT	account	Office Supplies	60340	2022-09-20 08:40:13.410778+00	2022-09-20 08:40:13.410806+00	1	t	{"account_type": "incomestatement"}	f	\N
761	ACCOUNT	account	Rent	60300	2022-09-20 08:40:13.410861+00	2022-09-20 08:40:13.410889+00	1	t	{"account_type": "incomestatement"}	f	\N
762	ACCOUNT	account	COGS - Subcontractors	50300	2022-09-20 08:40:13.410944+00	2022-09-20 08:40:13.410971+00	1	t	{"account_type": "incomestatement"}	f	\N
763	ACCOUNT	account	Contract Usage - Unbilled	40800-101	2022-09-20 08:40:13.411026+00	2022-09-20 08:40:13.411054+00	1	t	{"account_type": "incomestatement"}	f	\N
764	ACCOUNT	account	Contract Usage - Billed	40800-102	2022-09-20 08:40:13.411108+00	2022-09-20 08:40:13.411387+00	1	t	{"account_type": "incomestatement"}	f	\N
765	ACCOUNT	account	Contract Subscriptions - Unbilled	40600-101	2022-09-20 08:40:13.411479+00	2022-09-20 08:40:13.411508+00	1	t	{"account_type": "incomestatement"}	f	\N
766	ACCOUNT	account	OE Subscriptions	40500	2022-09-20 08:40:13.411563+00	2022-09-20 08:40:13.411591+00	1	t	{"account_type": "incomestatement"}	f	\N
767	ACCOUNT	account	Contract Subscriptions	40600	2022-09-20 08:40:13.411645+00	2022-09-20 08:40:13.411673+00	1	t	{"account_type": "incomestatement"}	f	\N
768	ACCOUNT	account	Contract Usage	40800	2022-09-20 08:40:13.411727+00	2022-09-20 08:40:13.411754+00	1	t	{"account_type": "incomestatement"}	f	\N
769	ACCOUNT	account	Contract Subscriptions - Billed	40600-102	2022-09-20 08:40:13.411808+00	2022-09-20 08:40:13.411835+00	1	t	{"account_type": "incomestatement"}	f	\N
770	ACCOUNT	account	Contract Usage - Paid	40800-103	2022-09-20 08:40:13.411889+00	2022-09-20 08:40:13.411916+00	1	t	{"account_type": "incomestatement"}	f	\N
771	ACCOUNT	account	Contract Subscriptions - Paid	40600-103	2022-09-20 08:40:13.41197+00	2022-09-20 08:40:13.411998+00	1	t	{"account_type": "incomestatement"}	f	\N
772	ACCOUNT	account	Contract Services - Billed	40700-102	2022-09-20 08:40:13.412052+00	2022-09-20 08:40:13.412079+00	1	t	{"account_type": "incomestatement"}	f	\N
773	ACCOUNT	account	Revenue - Services	40100	2022-09-20 08:40:13.412261+00	2022-09-20 08:40:13.412299+00	1	t	{"account_type": "incomestatement"}	f	\N
774	ACCOUNT	account	Revenue - Subcontractors	40300	2022-09-20 08:40:13.412353+00	2022-09-20 08:40:13.41238+00	1	t	{"account_type": "incomestatement"}	f	\N
775	ACCOUNT	account	Contract Services - Paid	40700-103	2022-09-20 08:40:13.412435+00	2022-09-20 08:40:13.412462+00	1	t	{"account_type": "incomestatement"}	f	\N
776	ACCOUNT	account	Revenue - Reimbursed Expenses	40200	2022-09-20 08:40:13.412516+00	2022-09-20 08:40:13.412543+00	1	t	{"account_type": "incomestatement"}	f	\N
777	ACCOUNT	account	Contract Services	40700	2022-09-20 08:40:13.412597+00	2022-09-20 08:40:13.412624+00	1	t	{"account_type": "incomestatement"}	f	\N
778	ACCOUNT	account	Contract Services - Unbilled	40700-101	2022-09-20 08:40:13.412678+00	2022-09-20 08:40:13.412705+00	1	t	{"account_type": "incomestatement"}	f	\N
779	ACCOUNT	account	Spot Bonus	60150	2022-09-20 08:40:13.412759+00	2022-09-20 08:40:13.412787+00	1	t	{"account_type": "incomestatement"}	f	\N
780	ACCOUNT	account	CTA	36000	2022-09-20 08:40:13.41284+00	2022-09-20 08:40:13.412868+00	1	t	{"account_type": "balancesheet"}	f	\N
781	ACCOUNT	account	COGS - Other	50900	2022-09-20 08:40:13.412922+00	2022-09-20 08:40:13.41295+00	1	t	{"account_type": "incomestatement"}	f	\N
782	ACCOUNT	account	Allowance For Doubtful Accounts	12200	2022-09-20 08:40:13.413004+00	2022-09-20 08:40:13.413032+00	1	t	{"account_type": "balancesheet"}	f	\N
783	ACCOUNT	account	Prepaid Insurance	14100	2022-09-20 08:40:13.413085+00	2022-09-20 08:40:13.413113+00	1	t	{"account_type": "balancesheet"}	f	\N
784	ACCOUNT	account	Prepaid Rent	14200	2022-09-20 08:40:13.413405+00	2022-09-20 08:40:13.413435+00	1	t	{"account_type": "balancesheet"}	f	\N
785	ACCOUNT	account	Prepaid Other	14300	2022-09-20 08:40:13.413489+00	2022-09-20 08:40:13.413517+00	1	t	{"account_type": "balancesheet"}	f	\N
786	ACCOUNT	account	Employee Advances	12500	2022-09-20 08:40:13.413571+00	2022-09-20 08:40:13.413598+00	1	t	{"account_type": "balancesheet"}	f	\N
787	ACCOUNT	account	Accrued Expense	20600	2022-09-20 08:40:13.413652+00	2022-09-20 08:40:13.41368+00	1	t	{"account_type": "balancesheet"}	f	\N
788	ACCOUNT	account	Inventory - GRNI	20680	2022-09-20 08:40:13.413734+00	2022-09-20 08:40:13.413761+00	1	t	{"account_type": "balancesheet"}	f	\N
789	ACCOUNT	account	Accrued Payroll Tax Payable	20650	2022-09-20 08:40:13.413815+00	2022-09-20 08:40:13.413843+00	1	t	{"account_type": "balancesheet"}	f	\N
790	ACCOUNT	account	Accr. Sales Tax Payable	20610	2022-09-20 08:40:13.413896+00	2022-09-20 08:40:13.413924+00	1	t	{"account_type": "balancesheet"}	f	\N
791	ACCOUNT	account	Bad Debt Expense	60650	2022-09-20 08:40:13.413979+00	2022-09-20 08:40:13.414006+00	1	t	{"account_type": "incomestatement"}	f	\N
792	ACCOUNT	account	Travel	60200	2022-09-20 08:40:13.41406+00	2022-09-20 08:40:13.414087+00	1	t	{"account_type": "incomestatement"}	f	\N
793	ACCOUNT	account	Interest Expense	70200	2022-09-20 08:40:13.414297+00	2022-09-20 08:40:13.414327+00	1	t	{"account_type": "incomestatement"}	f	\N
794	ACCOUNT	account	Other G&A	60660	2022-09-20 08:40:13.414386+00	2022-09-20 08:40:13.414415+00	1	t	{"account_type": "incomestatement"}	f	\N
795	ACCOUNT	account	Currency Gain-Loss	70500	2022-09-20 08:40:13.414472+00	2022-09-20 08:40:13.414511+00	1	t	{"account_type": "incomestatement"}	f	\N
796	ACCOUNT	account	Telecommunications	60220	2022-09-20 08:40:13.414566+00	2022-09-20 08:40:13.414593+00	1	t	{"account_type": "incomestatement"}	f	\N
797	ACCOUNT	account	Valuation Reserves	13500	2022-09-20 08:40:13.414647+00	2022-09-20 08:40:13.414674+00	1	t	{"account_type": "balancesheet"}	f	\N
798	ACCOUNT	account	Goodwill	16100	2022-09-20 08:40:13.414728+00	2022-09-20 08:40:13.414768+00	1	t	{"account_type": "balancesheet"}	f	\N
799	ACCOUNT	account	Depreciation Expense	60630	2022-09-20 08:40:13.414918+00	2022-09-20 08:40:13.414953+00	1	t	{"account_type": "incomestatement"}	f	\N
800	ACCOUNT	account	Printing and Reproduction	60360	2022-09-20 08:40:13.41501+00	2022-09-20 08:40:13.415038+00	1	t	{"account_type": "incomestatement"}	f	\N
801	ACCOUNT	account	Notes Payable	20200	2022-09-20 08:40:13.415092+00	2022-09-20 08:40:13.415141+00	1	t	{"account_type": "balancesheet"}	f	\N
802	ACCOUNT	account	Long Term Debt	20400	2022-09-20 08:40:13.415323+00	2022-09-20 08:40:13.415351+00	1	t	{"account_type": "balancesheet"}	f	\N
803	ACCOUNT	account	Unrealized Currency Gain and Loss	30310	2022-09-20 08:40:13.415405+00	2022-09-20 08:40:13.415433+00	1	t	{"account_type": "balancesheet"}	f	\N
804	ACCOUNT	account	Trade Shows and Exhibits	60510	2022-09-20 08:40:13.415487+00	2022-09-20 08:40:13.415515+00	1	t	{"account_type": "incomestatement"}	f	\N
805	ACCOUNT	account	Marketing and Advertising	60500	2022-09-20 08:40:13.422642+00	2022-09-20 08:40:13.422714+00	1	t	{"account_type": "incomestatement"}	f	\N
806	ACCOUNT	account	Insurance	60330	2022-09-20 08:40:13.422839+00	2022-09-20 08:40:13.423003+00	1	t	{"account_type": "incomestatement"}	f	\N
807	ACCOUNT	account	Meals and Entertainment	60210	2022-09-20 08:40:13.423097+00	2022-09-20 08:40:13.423151+00	1	t	{"account_type": "incomestatement"}	f	\N
808	ACCOUNT	account	Postage and Delivery	60350	2022-09-20 08:40:13.423343+00	2022-09-20 08:40:13.423371+00	1	t	{"account_type": "incomestatement"}	f	\N
809	ACCOUNT	account	Professional Fees Expense	60410	2022-09-20 08:40:13.423427+00	2022-09-20 08:40:13.423454+00	1	t	{"account_type": "incomestatement"}	f	\N
810	ACCOUNT	account	Repairs and Maintenance	60320	2022-09-20 08:40:13.42351+00	2022-09-20 08:40:13.423538+00	1	t	{"account_type": "incomestatement"}	f	\N
811	ACCOUNT	account	Salaries and Wages	60100	2022-09-20 08:40:13.423593+00	2022-09-20 08:40:13.42362+00	1	t	{"account_type": "incomestatement"}	f	\N
812	ACCOUNT	account	Gain for Sale of an Asset	80500	2022-09-20 08:40:13.423675+00	2022-09-20 08:40:13.423702+00	1	t	{"account_type": "incomestatement"}	f	\N
813	ACCOUNT	account	Dividends	80400	2022-09-20 08:40:13.423757+00	2022-09-20 08:40:13.423784+00	1	t	{"account_type": "incomestatement"}	f	\N
814	ACCOUNT	account	Cash	10100	2022-09-20 08:40:13.423839+00	2022-09-20 08:40:13.423866+00	1	t	{"account_type": "balancesheet"}	f	\N
815	ACCOUNT	account	Checking 4 - Bank Of Canada	10040	2022-09-20 08:40:13.423921+00	2022-09-20 08:40:13.423949+00	1	t	{"account_type": "balancesheet"}	f	\N
816	ACCOUNT	account	Checking 5 - Bank Of England	10050	2022-09-20 08:40:13.424113+00	2022-09-20 08:40:13.424153+00	1	t	{"account_type": "balancesheet"}	f	\N
817	ACCOUNT	account	Checking 6 - Bank Of Australia	10060	2022-09-20 08:40:13.424219+00	2022-09-20 08:40:13.424368+00	1	t	{"account_type": "balancesheet"}	f	\N
818	ACCOUNT	account	Checking 7 - Bank Of South Africa	10070	2022-09-20 08:40:13.424435+00	2022-09-20 08:40:13.424463+00	1	t	{"account_type": "balancesheet"}	f	\N
819	ACCOUNT	account	Investments and Securities	10400	2022-09-20 08:40:13.424517+00	2022-09-20 08:40:13.424545+00	1	t	{"account_type": "balancesheet"}	f	\N
820	ACCOUNT	account	Checking 1 - SVB	10010	2022-09-20 08:40:13.424599+00	2022-09-20 08:40:13.424627+00	1	t	{"account_type": "balancesheet"}	f	\N
821	ACCOUNT	account	Checking 2 - SVB	10020	2022-09-20 08:40:13.42468+00	2022-09-20 08:40:13.424708+00	1	t	{"account_type": "balancesheet"}	f	\N
822	ACCOUNT	account	Checking 3 - SVB	10030	2022-09-20 08:40:13.424762+00	2022-09-20 08:40:13.42479+00	1	t	{"account_type": "balancesheet"}	f	\N
823	ACCOUNT	account	Due from Entity 400	12900-400	2022-09-20 08:40:13.424844+00	2022-09-20 08:40:13.424871+00	1	t	{"account_type": "balancesheet"}	f	\N
824	ACCOUNT	account	Due from Entity 700	12900-700	2022-09-20 08:40:13.424925+00	2022-09-20 08:40:13.424952+00	1	t	{"account_type": "balancesheet"}	f	\N
825	ACCOUNT	account	Due from Entity 600	12900-600	2022-09-20 08:40:13.425005+00	2022-09-20 08:40:13.425033+00	1	t	{"account_type": "balancesheet"}	f	\N
826	ACCOUNT	account	Due from Entity 500	12900-500	2022-09-20 08:40:13.425086+00	2022-09-20 08:40:13.425328+00	1	t	{"account_type": "balancesheet"}	f	\N
827	ACCOUNT	account	Due from Entity 200	12900-200	2022-09-20 08:40:13.425398+00	2022-09-20 08:40:13.425426+00	1	t	{"account_type": "balancesheet"}	f	\N
828	ACCOUNT	account	Due from Entity 300	12900-300	2022-09-20 08:40:13.425479+00	2022-09-20 08:40:13.425507+00	1	t	{"account_type": "balancesheet"}	f	\N
829	ACCOUNT	account	Due from Entity 100	12900-100	2022-09-20 08:40:13.425595+00	2022-09-20 08:40:13.425662+00	1	t	{"account_type": "balancesheet"}	f	\N
830	ACCOUNT	account	Intercompany Receivables	12900	2022-09-20 08:40:13.425753+00	2022-09-20 08:40:13.425774+00	1	t	{"account_type": "balancesheet"}	f	\N
831	ACCOUNT	account	Unbilled AR - Contract Services	12701-200	2022-09-20 08:40:13.425824+00	2022-09-20 08:40:13.425854+00	1	t	{"account_type": "balancesheet"}	f	\N
832	ACCOUNT	account	Unbilled AR - Contract Usage	12701-300	2022-09-20 08:40:13.425909+00	2022-09-20 08:40:13.425927+00	1	t	{"account_type": "balancesheet"}	f	\N
833	ACCOUNT	account	Deferred Expense - Commission	17710-001	2022-09-20 08:40:13.425973+00	2022-09-20 08:40:13.426002+00	1	t	{"account_type": "balancesheet"}	f	\N
834	ACCOUNT	account	Deferred Expense - Royalty	17710-002	2022-09-20 08:40:13.426059+00	2022-09-20 08:40:13.426178+00	1	t	{"account_type": "balancesheet"}	f	\N
835	ACCOUNT	account	Tax Receivable	12620	2022-09-20 08:40:13.426227+00	2022-09-20 08:40:13.426248+00	1	t	{"account_type": "balancesheet"}	f	\N
836	ACCOUNT	account	Deferred Expense	17710	2022-09-20 08:40:13.426305+00	2022-09-20 08:40:13.426335+00	1	t	{"account_type": "balancesheet"}	f	\N
837	ACCOUNT	account	Unbilled AR - Contract Subscriptions	12701-100	2022-09-20 08:40:13.426688+00	2022-09-20 08:40:13.426707+00	1	t	{"account_type": "balancesheet"}	f	\N
838	ACCOUNT	account	WIP (Labor Only)	12600	2022-09-20 08:40:13.426754+00	2022-09-20 08:40:13.426778+00	1	t	{"account_type": "balancesheet"}	f	\N
839	ACCOUNT	account	Unbilled AR	12701	2022-09-20 08:40:13.426822+00	2022-09-20 08:40:13.426837+00	1	t	{"account_type": "balancesheet"}	f	\N
840	ACCOUNT	account	Buildings Accm. Depr.	15110	2022-09-20 08:40:13.426883+00	2022-09-20 08:40:13.426922+00	1	t	{"account_type": "balancesheet"}	f	\N
841	ACCOUNT	account	Capitalized Software Costs	16300	2022-09-20 08:40:13.427102+00	2022-09-20 08:40:13.427141+00	1	t	{"account_type": "balancesheet"}	f	\N
842	ACCOUNT	account	Buildings	15100	2022-09-20 08:40:13.427196+00	2022-09-20 08:40:13.427223+00	1	t	{"account_type": "balancesheet"}	f	\N
843	ACCOUNT	account	DR - Contract Subscriptions - Unbilled	20701-101	2022-09-20 08:40:13.427278+00	2022-09-20 08:40:13.427305+00	1	t	{"account_type": "balancesheet"}	f	\N
844	ACCOUNT	account	DR - Contract Usage - Unbilled	20701-301	2022-09-20 08:40:13.427359+00	2022-09-20 08:40:13.427387+00	1	t	{"account_type": "balancesheet"}	f	\N
845	ACCOUNT	account	DR - Contract Subscriptions - Billed	20701-102	2022-09-20 08:40:13.427441+00	2022-09-20 08:40:13.427468+00	1	t	{"account_type": "balancesheet"}	f	\N
846	ACCOUNT	account	DR - Contract Services - Billed	20701-202	2022-09-20 08:40:13.427522+00	2022-09-20 08:40:13.42755+00	1	t	{"account_type": "balancesheet"}	f	\N
847	ACCOUNT	account	DR - Contract Usage - Billed	20701-302	2022-09-20 08:40:13.427637+00	2022-09-20 08:40:13.427727+00	1	t	{"account_type": "balancesheet"}	f	\N
848	ACCOUNT	account	DR - Contract Usage - Paid	20701-303	2022-09-20 08:40:13.427793+00	2022-09-20 08:40:13.427821+00	1	t	{"account_type": "balancesheet"}	f	\N
849	ACCOUNT	account	DR - Contract Services - Paid	20701-203	2022-09-20 08:40:13.427875+00	2022-09-20 08:40:13.427903+00	1	t	{"account_type": "balancesheet"}	f	\N
850	ACCOUNT	account	DR - Contract Subscriptions - Paid	20701-103	2022-09-20 08:40:13.427957+00	2022-09-20 08:40:13.427985+00	1	t	{"account_type": "balancesheet"}	f	\N
851	ACCOUNT	account	DR - Contract Services - Unbilled	20701-201	2022-09-20 08:40:13.428038+00	2022-09-20 08:40:13.428066+00	1	t	{"account_type": "balancesheet"}	f	\N
852	ACCOUNT	account	Deferred Revenue Contra	20702	2022-09-20 08:40:13.42812+00	2022-09-20 08:40:13.428147+00	1	t	{"account_type": "balancesheet"}	f	\N
853	ACCOUNT	account	Deferred Revenue	20701	2022-09-20 08:40:13.428318+00	2022-09-20 08:40:13.428346+00	1	t	{"account_type": "balancesheet"}	f	\N
854	ACCOUNT	account	Due to Entity 700	20900-700	2022-09-20 08:40:13.428399+00	2022-09-20 08:40:13.428427+00	1	t	{"account_type": "balancesheet"}	f	\N
855	ACCOUNT	account	Due to Entity 500	20900-500	2022-09-20 08:40:13.434257+00	2022-09-20 08:40:13.4343+00	1	t	{"account_type": "balancesheet"}	f	\N
856	ACCOUNT	account	Due to Entity 400	20900-400	2022-09-20 08:40:13.434366+00	2022-09-20 08:40:13.434395+00	1	t	{"account_type": "balancesheet"}	f	\N
857	ACCOUNT	account	Due to Entity 600	20900-600	2022-09-20 08:40:13.434453+00	2022-09-20 08:40:13.434481+00	1	t	{"account_type": "balancesheet"}	f	\N
858	ACCOUNT	account	Due to Entity 300	20900-300	2022-09-20 08:40:13.434538+00	2022-09-20 08:40:13.434566+00	1	t	{"account_type": "balancesheet"}	f	\N
859	ACCOUNT	account	Due to Entity 100	20900-100	2022-09-20 08:40:13.434622+00	2022-09-20 08:40:13.43465+00	1	t	{"account_type": "balancesheet"}	f	\N
860	ACCOUNT	account	Due to Entity 200	20900-200	2022-09-20 08:40:13.434705+00	2022-09-20 08:40:13.434733+00	1	t	{"account_type": "balancesheet"}	f	\N
861	ACCOUNT	account	Intercompany Payables	20900	2022-09-20 08:40:13.434788+00	2022-09-20 08:40:13.434815+00	1	t	{"account_type": "balancesheet"}	f	\N
862	ACCOUNT	account	Interest Income	80200	2022-09-20 08:40:13.43487+00	2022-09-20 08:40:13.434898+00	1	t	{"account_type": "incomestatement"}	f	\N
863	ACCOUNT	account	Journal Entry Rounding	70400	2022-09-20 08:40:13.434953+00	2022-09-20 08:40:13.43498+00	1	t	{"account_type": "incomestatement"}	f	\N
864	ACCOUNT	account	Intercompany Professional Fees	40400	2022-09-20 08:40:13.435035+00	2022-09-20 08:40:13.435062+00	1	t	{"account_type": "incomestatement"}	f	\N
865	ACCOUNT	account	Accumulated OCI	30300	2022-09-20 08:40:13.435117+00	2022-09-20 08:40:13.435773+00	1	t	{"account_type": "balancesheet"}	f	\N
866	ACCOUNT	account	Amortization Expense	60640	2022-09-20 08:40:13.43647+00	2022-09-20 08:40:13.436515+00	1	t	{"account_type": "incomestatement"}	f	\N
867	ACCOUNT	account	Revenue - Other	40900	2022-09-20 08:40:13.436692+00	2022-09-20 08:40:13.436726+00	1	t	{"account_type": "incomestatement"}	f	\N
868	ACCOUNT	account	Employee Deductions	60140	2022-09-20 08:40:13.436794+00	2022-09-20 08:40:13.436824+00	1	t	{"account_type": "incomestatement"}	f	\N
869	ACCOUNT	account	Payroll Taxes	60130	2022-09-20 08:40:13.436889+00	2022-09-20 08:40:13.436919+00	1	t	{"account_type": "incomestatement"}	f	\N
870	ACCOUNT	account	Other Taxes	60620	2022-09-20 08:40:13.43698+00	2022-09-20 08:40:13.43701+00	1	t	{"account_type": "incomestatement"}	f	\N
871	ACCOUNT	account	Excise Tax	60610	2022-09-20 08:40:13.437256+00	2022-09-20 08:40:13.437289+00	1	t	{"account_type": "incomestatement"}	f	\N
872	ACCOUNT	account	Reserved Inventory	13400	2022-09-20 08:40:13.437352+00	2022-09-20 08:40:13.437381+00	1	t	{"account_type": "balancesheet"}	f	\N
873	ACCOUNT	account	Supplies	13300	2022-09-20 08:40:13.437443+00	2022-09-20 08:40:13.437473+00	1	t	{"account_type": "balancesheet"}	f	\N
874	ACCOUNT	account	Goods in Transit	13200	2022-09-20 08:40:13.437558+00	2022-09-20 08:40:13.437602+00	1	t	{"account_type": "balancesheet"}	f	\N
875	ACCOUNT	account	Inventory	13100	2022-09-20 08:40:13.437946+00	2022-09-20 08:40:13.438066+00	1	t	{"account_type": "balancesheet"}	f	\N
876	ACCOUNT	account	Inventory - Other	13900	2022-09-20 08:40:13.43814+00	2022-09-20 08:40:13.438171+00	1	t	{"account_type": "balancesheet"}	f	\N
877	ACCOUNT	account	Other Intangible Assets	16900	2022-09-20 08:40:13.438466+00	2022-09-20 08:40:13.438489+00	1	t	{"account_type": "balancesheet"}	f	\N
878	ACCOUNT	account	Other Assets	17000	2022-09-20 08:40:13.43854+00	2022-09-20 08:40:13.438569+00	1	t	{"account_type": "balancesheet"}	f	\N
879	ACCOUNT	account	Credit Card Offset	20500	2022-09-20 08:40:13.438632+00	2022-09-20 08:40:13.438655+00	1	t	{"account_type": "balancesheet"}	f	\N
880	ACCOUNT	account	Sales Tax Payable	20620	2022-09-20 08:40:13.438713+00	2022-09-20 08:40:13.438742+00	1	t	{"account_type": "balancesheet"}	f	\N
881	ACCOUNT	account	Common Stock	30100	2022-09-20 08:40:13.438801+00	2022-09-20 08:40:13.43884+00	1	t	{"account_type": "balancesheet"}	f	\N
882	ACCOUNT	account	Preferred Stock	30200	2022-09-20 08:40:13.438895+00	2022-09-20 08:40:13.438922+00	1	t	{"account_type": "balancesheet"}	f	\N
883	ACCOUNT	account	Retained Earnings	35000	2022-09-20 08:40:13.438987+00	2022-09-20 08:40:13.439129+00	1	t	{"account_type": "balancesheet"}	f	\N
884	ACCOUNT	account	COGS - Materials	50200	2022-09-20 08:40:13.439188+00	2022-09-20 08:40:13.439227+00	1	t	{"account_type": "incomestatement"}	f	\N
885	ACCOUNT	account	Paid Time Off	70303	2022-09-20 08:40:13.439282+00	2022-09-20 08:40:13.439309+00	1	t	{"account_type": "incomestatement"}	f	\N
886	ACCOUNT	account	Indirect Labor	70300	2022-09-20 08:40:13.439364+00	2022-09-20 08:40:13.439391+00	1	t	{"account_type": "incomestatement"}	f	\N
887	ACCOUNT	account	Holiday	70301	2022-09-20 08:40:13.439446+00	2022-09-20 08:40:13.439473+00	1	t	{"account_type": "incomestatement"}	f	\N
888	ACCOUNT	account	Company Credit Card Offset	60700	2022-09-20 08:40:13.439527+00	2022-09-20 08:40:13.439555+00	1	t	{"account_type": "incomestatement"}	f	\N
889	ACCOUNT	account	Other Expense	70100	2022-09-20 08:40:13.439609+00	2022-09-20 08:40:13.439636+00	1	t	{"account_type": "incomestatement"}	f	\N
890	ACCOUNT	account	Professional Development	70302	2022-09-20 08:40:13.439691+00	2022-09-20 08:40:13.439719+00	1	t	{"account_type": "incomestatement"}	f	\N
891	ACCOUNT	account	Indirect Labor Offset	70304	2022-09-20 08:40:13.439773+00	2022-09-20 08:40:13.439801+00	1	t	{"account_type": "incomestatement"}	f	\N
892	ACCOUNT	account	Other Income	80100	2022-09-20 08:40:13.439855+00	2022-09-20 08:40:13.439883+00	1	t	{"account_type": "incomestatement"}	f	\N
893	ACCOUNT	account	AR - Retainage	12710	2022-09-20 08:40:13.439937+00	2022-09-20 08:40:13.439965+00	1	t	{"account_type": "balancesheet"}	f	\N
894	ACCOUNT	account	Accounts Receivable	12100	2022-09-20 08:40:13.440019+00	2022-09-20 08:40:13.440046+00	1	t	{"account_type": "balancesheet"}	f	\N
895	ACCOUNT	account	Accounts Payable - Employees	20300	2022-09-20 08:40:13.4401+00	2022-09-20 08:40:13.440127+00	1	t	{"account_type": "balancesheet"}	f	\N
896	ACCOUNT	account	Accounts Payable	20100	2022-09-20 08:40:13.440306+00	2022-09-20 08:40:13.440346+00	1	t	{"account_type": "balancesheet"}	f	\N
897	ACCOUNT	account	Billable Overtime Hours	51708	2022-09-20 08:40:13.440401+00	2022-09-20 08:40:13.440428+00	1	t	{"account_type": "incomestatement"}	f	\N
898	ACCOUNT	account	Non-Billable Overtime Hours	51709	2022-09-20 08:40:13.440482+00	2022-09-20 08:40:13.44051+00	1	t	{"account_type": "incomestatement"}	f	\N
899	ACCOUNT	account	Billable Hours	51701	2022-09-20 08:40:13.440564+00	2022-09-20 08:40:13.440591+00	1	t	{"account_type": "incomestatement"}	f	\N
900	ACCOUNT	account	Labor Cost Variance	51711	2022-09-20 08:40:13.440646+00	2022-09-20 08:40:13.440673+00	1	t	{"account_type": "incomestatement"}	f	\N
901	ACCOUNT	account	Labor Cost Offset	51710	2022-09-20 08:40:13.440829+00	2022-09-20 08:40:13.440863+00	1	t	{"account_type": "incomestatement"}	f	\N
902	ACCOUNT	account	Non-Billable Hours	51702	2022-09-20 08:40:13.440923+00	2022-09-20 08:40:13.440951+00	1	t	{"account_type": "incomestatement"}	f	\N
903	ACCOUNT	account	COGS - Burden on Projects	51703	2022-09-20 08:40:13.441005+00	2022-09-20 08:40:13.441033+00	1	t	{"account_type": "incomestatement"}	f	\N
904	ACCOUNT	account	COGS - Overhead on Projects	51704	2022-09-20 08:40:13.441087+00	2022-09-20 08:40:13.441257+00	1	t	{"account_type": "incomestatement"}	f	\N
905	ACCOUNT	account	COGS - G&A on Projects	51705	2022-09-20 08:40:13.44715+00	2022-09-20 08:40:13.447201+00	1	t	{"account_type": "incomestatement"}	f	\N
906	ACCOUNT	account	COGS - Indirect Projects Costs Offset	51706	2022-09-20 08:40:13.447282+00	2022-09-20 08:40:13.447329+00	1	t	{"account_type": "incomestatement"}	f	\N
907	ACCOUNT	account	COGS - Reimbursed Expenses	51707	2022-09-20 08:40:13.447396+00	2022-09-20 08:40:13.447423+00	1	t	{"account_type": "incomestatement"}	f	\N
908	ACCOUNT	account	Software and Licenses	60400	2022-09-20 08:40:13.447468+00	2022-09-20 08:40:13.447489+00	1	t	{"account_type": "incomestatement"}	f	\N
909	ACCOUNT	account	Utilities	60310	2022-09-20 08:40:13.447542+00	2022-09-20 08:40:13.447553+00	1	t	{"account_type": "incomestatement"}	f	\N
910	ACCOUNT	account	Downgrade	90006	2022-09-20 08:40:13.447601+00	2022-09-20 08:40:13.447626+00	1	t	{"account_type": "balancesheet"}	f	\N
911	ACCOUNT	account	Contract Royalty Expense	50400	2022-09-20 08:40:13.447676+00	2022-09-20 08:40:13.447714+00	1	t	{"account_type": "incomestatement"}	f	\N
912	ACCOUNT	account	Contract Commission	60160	2022-09-20 08:40:13.447769+00	2022-09-20 08:40:13.447796+00	1	t	{"account_type": "incomestatement"}	f	\N
913	ACCOUNT	account	CMRR Offset	90009	2022-09-20 08:40:13.447851+00	2022-09-20 08:40:13.447878+00	1	t	{"account_type": "balancesheet"}	f	\N
914	ACCOUNT	account	CMRR New	90002	2022-09-20 08:40:13.447932+00	2022-09-20 08:40:13.447959+00	1	t	{"account_type": "balancesheet"}	f	\N
915	ACCOUNT	account	CMRR Add-On	90003	2022-09-20 08:40:13.448013+00	2022-09-20 08:40:13.44804+00	1	t	{"account_type": "balancesheet"}	f	\N
916	ACCOUNT	account	Renewal Upgrade	90004	2022-09-20 08:40:13.448094+00	2022-09-20 08:40:13.448232+00	1	t	{"account_type": "balancesheet"}	f	\N
917	ACCOUNT	account	Renewal Downgrade	90005	2022-09-20 08:40:13.448341+00	2022-09-20 08:40:13.44837+00	1	t	{"account_type": "balancesheet"}	f	\N
918	ACCOUNT	account	CMRR Churn	90007	2022-09-20 08:40:13.448425+00	2022-09-20 08:40:13.448452+00	1	t	{"account_type": "balancesheet"}	f	\N
919	ACCOUNT	account	CMRR Renewal	90008	2022-09-20 08:40:13.448506+00	2022-09-20 08:40:13.448533+00	1	t	{"account_type": "incomestatement"}	f	\N
920	ACCOUNT	account	nilewh	12221	2022-09-20 08:40:13.448587+00	2022-09-20 08:40:13.448614+00	1	t	{"account_type": "balancesheet"}	f	\N
921	ACCOUNT	account	Potential Billings	90000	2022-09-20 08:40:13.448668+00	2022-09-20 08:40:13.448695+00	1	t	{"account_type": "incomestatement"}	f	\N
922	ACCOUNT	account	Potential Billings Offset	90001	2022-09-20 08:40:13.448749+00	2022-09-20 08:40:13.448776+00	1	t	{"account_type": "incomestatement"}	f	\N
923	ACCOUNT	account	Elimination Adjustment	70600	2022-09-20 08:40:13.44883+00	2022-09-20 08:40:13.448857+00	1	t	{"account_type": "incomestatement"}	f	\N
924	ACCOUNT	account	Transactor Clearing	12610	2022-09-20 08:40:13.448911+00	2022-09-20 08:40:13.448939+00	1	t	{"account_type": "balancesheet"}	f	\N
925	EXPENSE_TYPE	Expense Types	Airfare	Airfare	2022-09-20 08:40:17.37637+00	2022-09-20 08:40:17.376416+00	1	t	{"gl_account_no": "60200", "gl_account_title": "Travel"}	f	\N
926	EXPENSE_TYPE	Expense Types	Cell Phone	Cell Phone	2022-09-20 08:40:17.3765+00	2022-09-20 08:40:17.376531+00	1	t	{"gl_account_no": "60220", "gl_account_title": "Telecommunications"}	f	\N
927	EXPENSE_TYPE	Expense Types	Ground Transportation-Parking	Ground Transportation/Parking	2022-09-20 08:40:17.376606+00	2022-09-20 08:40:17.376636+00	1	t	{"gl_account_no": "60200", "gl_account_title": "Travel"}	f	\N
928	EXPENSE_TYPE	Expense Types	Hotel-Lodging	Hotel/Lodging	2022-09-20 08:40:17.376707+00	2022-09-20 08:40:17.376737+00	1	t	{"gl_account_no": "60200", "gl_account_title": "Travel"}	f	\N
929	EXPENSE_TYPE	Expense Types	Internet	Internet	2022-09-20 08:40:17.376807+00	2022-09-20 08:40:17.376837+00	1	t	{"gl_account_no": "60220", "gl_account_title": "Telecommunications"}	f	\N
930	EXPENSE_TYPE	Expense Types	Meals	Meals	2022-09-20 08:40:17.376906+00	2022-09-20 08:40:17.376936+00	1	t	{"gl_account_no": "60210", "gl_account_title": "Meals and Entertainment"}	f	\N
931	EXPENSE_TYPE	Expense Types	Mileage	Mileage	2022-09-20 08:40:17.377005+00	2022-09-20 08:40:17.377034+00	1	t	{"gl_account_no": "60200", "gl_account_title": "Travel"}	f	\N
932	EXPENSE_TYPE	Expense Types	Per Diem	Per Diem	2022-09-20 08:40:17.377104+00	2022-09-20 08:40:17.377134+00	1	t	{"gl_account_no": "60210", "gl_account_title": "Meals and Entertainment"}	f	\N
\.


--
-- Data for Name: dimension_details; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.dimension_details (id, attribute_type, display_name, source_type, created_at, updated_at, workspace_id) FROM stdin;
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	contenttypes	contenttype
5	sessions	session
6	django_q	schedule
7	django_q	task
8	django_q	failure
9	django_q	success
10	django_q	ormq
11	fyle_rest_auth	authtoken
12	fyle_accounting_mappings	destinationattribute
13	fyle_accounting_mappings	expenseattribute
14	fyle_accounting_mappings	mappingsetting
15	fyle_accounting_mappings	mapping
16	fyle_accounting_mappings	employeemapping
17	fyle_accounting_mappings	categorymapping
18	users	user
19	workspaces	workspace
20	workspaces	sageintacctcredential
21	workspaces	fylecredential
22	workspaces	workspaceschedule
23	workspaces	configuration
24	fyle	expense
25	fyle	expensegroup
26	fyle	expensegroupsettings
27	fyle	reimbursement
28	sage_intacct	bill
29	sage_intacct	billlineitem
30	sage_intacct	expensereport
31	sage_intacct	expensereportlineitem
32	sage_intacct	chargecardtransaction
33	sage_intacct	chargecardtransactionlineitem
34	sage_intacct	appayment
35	sage_intacct	sageintacctreimbursement
36	sage_intacct	sageintacctreimbursementlineitem
37	sage_intacct	appaymentlineitem
38	sage_intacct	journalentry
39	sage_intacct	journalentrylineitem
40	tasks	tasklog
41	mappings	generalmapping
42	mappings	locationentitymapping
43	fyle_accounting_mappings	expensefield
44	fyle	expensefilter
45	fyle	dependentfieldsetting
46	sage_intacct	costtype
47	tasks	error
48	workspaces	lastexportdetail
49	fyle_integrations_imports	importlog
50	fyle_accounting_mappings	expenseattributesdeletioncache
51	common_resources	dimensiondetail
52	rabbitmq	failedevent
53	sage_intacct	costcode
54	workspaces	featureconfig
55	fyle_accounting_mappings	fylesynctimestamp
56	workspaces	intacctsyncedtimestamp
57	sage_intacct	sageintacctattributescount
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	users	0001_initial	2022-09-20 08:34:11.41152+00
2	contenttypes	0001_initial	2022-09-20 08:34:11.458906+00
3	admin	0001_initial	2022-09-20 08:34:11.499803+00
4	admin	0002_logentry_remove_auto_add	2022-09-20 08:34:11.537556+00
5	admin	0003_logentry_add_action_flag_choices	2022-09-20 08:34:11.553518+00
6	contenttypes	0002_remove_content_type_name	2022-09-20 08:34:11.594614+00
7	auth	0001_initial	2022-09-20 08:34:11.66851+00
8	auth	0002_alter_permission_name_max_length	2022-09-20 08:34:11.772457+00
9	auth	0003_alter_user_email_max_length	2022-09-20 08:34:11.785856+00
10	auth	0004_alter_user_username_opts	2022-09-20 08:34:11.79923+00
11	auth	0005_alter_user_last_login_null	2022-09-20 08:34:11.813922+00
12	auth	0006_require_contenttypes_0002	2022-09-20 08:34:11.821155+00
13	auth	0007_alter_validators_add_error_messages	2022-09-20 08:34:11.832817+00
14	auth	0008_alter_user_username_max_length	2022-09-20 08:34:11.850937+00
15	auth	0009_alter_user_last_name_max_length	2022-09-20 08:34:11.866633+00
16	auth	0010_alter_group_name_max_length	2022-09-20 08:34:11.891971+00
17	auth	0011_update_proxy_permissions	2022-09-20 08:34:11.949357+00
18	auth	0012_alter_user_first_name_max_length	2022-09-20 08:34:11.963037+00
19	django_q	0001_initial	2022-09-20 08:34:12.013497+00
20	django_q	0002_auto_20150630_1624	2022-09-20 08:34:12.060451+00
21	django_q	0003_auto_20150708_1326	2022-09-20 08:34:12.138208+00
22	django_q	0004_auto_20150710_1043	2022-09-20 08:34:12.210579+00
23	django_q	0005_auto_20150718_1506	2022-09-20 08:34:12.291295+00
24	django_q	0006_auto_20150805_1817	2022-09-20 08:34:12.340214+00
25	django_q	0007_ormq	2022-09-20 08:34:12.391175+00
26	django_q	0008_auto_20160224_1026	2022-09-20 08:34:12.402713+00
27	django_q	0009_auto_20171009_0915	2022-09-20 08:34:12.438764+00
28	django_q	0010_auto_20200610_0856	2022-09-20 08:34:12.464173+00
29	django_q	0011_auto_20200628_1055	2022-09-20 08:34:12.47932+00
30	django_q	0012_auto_20200702_1608	2022-09-20 08:34:12.490963+00
31	django_q	0013_task_attempt_count	2022-09-20 08:34:12.50976+00
32	workspaces	0001_initial	2022-09-20 08:34:12.698353+00
33	workspaces	0002_ccc	2022-09-20 08:34:12.813643+00
34	workspaces	0003_workspaceschedule	2022-09-20 08:34:12.937659+00
35	workspaces	0004_auto_20201228_0802	2022-09-20 08:34:12.977791+00
36	workspaces	0005_workspacegeneralsettings_import_projects	2022-09-20 08:34:13.010722+00
37	workspaces	0006_auto_20210208_0548	2022-09-20 08:34:13.042948+00
38	workspaces	0007_workspacegeneralsettings_auto_map_employees	2022-09-20 08:34:13.059131+00
39	workspaces	0008_workspacegeneralsettings_import_categories	2022-09-20 08:34:13.078101+00
40	workspaces	0009_workspacegeneralsettings_auto_create_destination_entity	2022-09-20 08:34:13.108958+00
41	workspaces	0010_auto_20210422_0817	2022-09-20 08:34:13.159052+00
42	workspaces	0011_workspace_cluster_domain	2022-09-20 08:34:13.192296+00
43	workspaces	0012_auto_20210723_0925	2022-09-20 08:34:13.249349+00
44	workspaces	0013_auto_20210723_1010	2022-09-20 08:34:13.301691+00
45	fyle	0001_initial	2022-09-20 08:34:13.436677+00
46	fyle	0002_fund_source	2022-09-20 08:34:13.786046+00
47	fyle	0003_expensegroup_exported_at	2022-09-20 08:34:13.826998+00
48	fyle	0004_auto_20201209_0558	2022-09-20 08:34:14.025983+00
49	fyle	0005_expense_billable	2022-09-20 08:34:14.045523+00
50	fyle	0006_auto_20210208_0548	2022-09-20 08:34:14.157745+00
51	fyle	0007_expense_org_id	2022-09-20 08:34:14.190587+00
52	fyle	0008_reimbursement_payment_number	2022-09-20 08:34:14.213617+00
53	fyle	0009_auto_20210917_0822	2022-09-20 08:34:14.239619+00
54	fyle	0010_auto_20211001_0525	2022-09-20 08:34:14.313223+00
55	fyle	0011_auto_20211203_1156	2022-09-20 08:34:14.396928+00
56	fyle	0012_auto_20220210_1106	2022-09-20 08:34:14.418038+00
57	fyle	0013_auto_20220510_1635	2022-09-20 08:34:14.456936+00
58	fyle	0014_expensegroupsettings_import_card_credits	2022-09-20 08:34:14.481284+00
59	fyle_accounting_mappings	0001_initial	2022-09-20 08:34:14.733253+00
60	fyle_accounting_mappings	0002_auto_20201117_0655	2022-09-20 08:34:15.21232+00
61	fyle_accounting_mappings	0003_auto_20201221_1244	2022-09-20 08:34:15.319885+00
62	fyle_accounting_mappings	0004_auto_20210127_1241	2022-09-20 08:34:15.394993+00
63	fyle_accounting_mappings	0005_expenseattribute_auto_mapped	2022-09-20 08:34:15.432968+00
64	fyle_accounting_mappings	0006_auto_20210305_0827	2022-09-20 08:34:15.51047+00
65	fyle_accounting_mappings	0007_auto_20210409_1931	2022-09-20 08:34:15.593389+00
66	fyle_accounting_mappings	0008_auto_20210604_0713	2022-09-20 08:34:15.913364+00
67	fyle_accounting_mappings	0009_auto_20210618_1004	2022-09-20 08:34:16.733441+00
68	fyle_accounting_mappings	0010_remove_mappingsetting_expense_field_id	2022-09-20 08:34:17.025427+00
69	fyle_accounting_mappings	0011_categorymapping_employeemapping	2022-09-20 08:34:17.278719+00
70	fyle_accounting_mappings	0012_auto_20211206_0600	2022-09-20 08:34:17.424863+00
71	fyle_accounting_mappings	0013_auto_20220323_1133	2022-09-20 08:34:17.515735+00
72	fyle_accounting_mappings	0014_mappingsetting_source_placeholder	2022-09-20 08:34:17.602735+00
73	fyle_accounting_mappings	0015_auto_20220412_0614	2022-09-20 08:34:17.839639+00
74	fyle_accounting_mappings	0016_auto_20220413_1624	2022-09-20 08:34:18.022281+00
75	fyle_accounting_mappings	0017_auto_20220419_0649	2022-09-20 08:34:18.731774+00
76	fyle_accounting_mappings	0018_auto_20220419_0709	2022-09-20 08:34:19.06654+00
77	fyle_rest_auth	0001_initial	2022-09-20 08:34:19.416057+00
78	fyle_rest_auth	0002_auto_20200101_1205	2022-09-20 08:34:19.51786+00
79	fyle_rest_auth	0003_auto_20200107_0921	2022-09-20 08:34:19.626702+00
80	fyle_rest_auth	0004_auto_20200107_1345	2022-09-20 08:34:19.946828+00
81	fyle_rest_auth	0005_remove_authtoken_access_token	2022-09-20 08:34:20.077756+00
82	fyle_rest_auth	0006_auto_20201221_0849	2022-09-20 08:34:20.237855+00
83	workspaces	0014_configuration_memo_structure	2022-09-20 08:34:20.433425+00
84	workspaces	0015_auto_20211229_1347	2022-09-20 08:34:20.489725+00
85	workspaces	0016_fylecredential_cluster_domain	2022-09-20 08:34:20.548133+00
86	workspaces	0017_configuration_import_tax_codes	2022-09-20 08:34:20.795793+00
87	mappings	0001_initial	2022-09-20 08:34:21.168003+00
88	mappings	0002_ccc	2022-09-20 08:34:21.416857+00
89	mappings	0003_auto_20210127_1551	2022-09-20 08:34:21.847549+00
90	mappings	0004_auto_20210208_0548	2022-09-20 08:34:22.499943+00
91	mappings	0005_auto_20210517_1650	2022-09-20 08:34:23.334661+00
92	mappings	0006_auto_20210603_0819	2022-09-20 08:34:23.580025+00
93	mappings	0007_auto_20210705_0933	2022-09-20 08:34:23.692476+00
94	mappings	0008_auto_20210831_0718	2022-09-20 08:34:23.776964+00
95	mappings	0009_auto_20220215_1553	2022-09-20 08:34:23.84625+00
96	mappings	0010_locationentitymapping	2022-09-20 08:34:23.919376+00
97	sage_intacct	0001_initial	2022-09-20 08:34:25.419418+00
98	sage_intacct	0002_charge_card_transactions	2022-09-20 08:34:27.477472+00
99	sage_intacct	0003_auto_20201209_0558	2022-09-20 08:34:28.695917+00
100	sage_intacct	0004_auto_20210127_1345	2022-09-20 08:34:29.947749+00
101	sage_intacct	0005_auto_20210208_0548	2022-09-20 08:34:32.634877+00
102	sage_intacct	0006_auto_20210224_0816	2022-09-20 08:34:33.370793+00
103	sage_intacct	0007_auto_20210308_0759	2022-09-20 08:34:35.042+00
104	sage_intacct	0008_auto_20210408_0812	2022-09-20 08:34:35.105949+00
105	sage_intacct	0009_auto_20210521_1008	2022-09-20 08:34:35.158518+00
106	sage_intacct	0010_expensereportlineitem_expense_payment_type	2022-09-20 08:34:35.18885+00
107	sage_intacct	0011_billlineitem_class_id	2022-09-20 08:34:35.254919+00
108	sage_intacct	0012_auto_20210907_0725	2022-09-20 08:34:35.358296+00
109	sage_intacct	0013_auto_20211203_1156	2022-09-20 08:34:35.422581+00
110	sage_intacct	0014_journalentry_journalentrylineitem	2022-09-20 08:34:36.915714+00
111	sage_intacct	0015_auto_20220103_0843	2022-09-20 08:34:37.395488+00
112	sage_intacct	0016_chargecardtransaction_payee	2022-09-20 08:34:37.46471+00
113	sage_intacct	0017_auto_20220210_1106	2022-09-20 08:34:37.893335+00
114	sessions	0001_initial	2022-09-20 08:34:37.975807+00
115	tasks	0001_initial	2022-09-20 08:34:39.601893+00
116	tasks	0002_charge_card_transactions	2022-09-20 08:34:41.715034+00
117	tasks	0003_auto_20210208_0548	2022-09-20 08:34:42.509343+00
118	tasks	0004_auto_20211203_1156	2022-09-20 08:34:44.935744+00
119	tasks	0005_tasklog_journal_entry	2022-09-20 08:34:45.270842+00
120	users	0002_auto_20201228_0802	2022-09-20 08:34:45.316135+00
121	workspaces	0018_auto_20220427_1043	2022-09-20 08:34:46.055545+00
122	workspaces	0019_auto_20220510_1635	2022-09-20 08:34:46.502776+00
123	workspaces	0020_configuration_change_accounting_period	2022-09-20 08:34:47.001754+00
124	workspaces	0021_configuration_import_vendors_as_merchants	2022-09-20 08:34:47.365985+00
125	workspaces	0022_configuration_employee_field_mapping	2022-09-20 08:34:47.637128+00
126	fyle	0015_expensegroup_export_type	2022-09-29 12:08:22.995468+00
127	fyle	0016_auto_20221213_0857	2022-12-15 06:54:10.950799+00
999	mappings	0011_auto_20221010_0741	2022-09-20 08:34:23.84625+00
128	sage_intacct	0018_auto_20221213_0819	2022-12-15 07:29:38.157471+00
129	sage_intacct	0018_auto_20221209_0901	2022-12-15 07:29:38.245266+00
130	sage_intacct	0019_merge_20221213_0857	2022-12-15 07:29:38.258629+00
131	workspaces	0023_auto_20221213_0857	2022-12-15 07:29:38.367282+00
132	fyle_accounting_mappings	0019_auto_20230105_1104	2023-03-13 06:15:36.100493+00
133	fyle_accounting_mappings	0020_auto_20230302_0519	2023-03-13 06:15:36.138972+00
134	sage_intacct	0019_auto_20230307_1746	2023-03-13 06:15:36.189955+00
135	workspaces	0024_auto_20230321_0740	2023-03-22 11:16:13.216068+00
136	fyle_accounting_mappings	0021_auto_20230323_0557	2023-04-10 09:54:41.984483+00
137	fyle	0017_expense_corporate_card_id	2023-04-14 10:35:13.275291+00
138	workspaces	0025_auto_20230417_1124	2023-04-17 11:42:04.893467+00
139	mappings	0012_auto_20230417_1124	2023-04-17 11:42:04.876255+00
140	fyle	0018_auto_20230427_0355	2023-04-27 03:56:21.411364+00
141	fyle	0019_expense_report_title	2023-04-27 16:57:27.877735+00
142	fyle	0020_dependentfield	2023-06-15 11:38:34.139106+00
143	fyle	0021_auto_20230615_0808	2023-06-15 11:38:34.1818+00
144	fyle_accounting_mappings	0022_auto_20230411_1118	2023-06-15 11:38:34.197521+00
145	sage_intacct	0020_costtypes	2023-06-15 11:38:34.218491+00
146	sage_intacct	0021_auto_20230608_1310	2023-06-15 11:38:34.25444+00
147	sage_intacct	0022_auto_20230615_1509	2023-06-15 15:10:11.18372+00
148	workspaces	0026_auto_20230531_0926	2023-06-21 10:38:21.962503+00
149	fyle	0022_auto_20230619_0812	2023-06-21 10:38:21.986148+00
150	fyle	0023_expense_posted_at	2023-06-21 10:38:21.992102+00
151	mappings	0013_auto_20230531_1040	2023-06-21 10:38:22.010068+00
152	mappings	0014_auto_20230531_1248	2023-06-21 10:38:22.030324+00
153	workspaces	0027_auto_20230614_1010	2023-06-21 10:38:22.056433+00
154	workspaces	0028_auto_20230620_0729	2023-06-21 10:38:22.076365+00
155	sage_intacct	0023_auto_20230626_1430	2023-06-27 10:58:25.589784+00
156	workspaces	0029_auto_20230630_1145	2023-06-30 15:03:32.662957+00
157	tasks	0006_error	2023-07-06 06:56:10.470672+00
158	fyle	0024_auto_20230705_1057	2023-07-06 05:38:46.331815+00
159	workspaces	0030_lastexportdetail	2023-07-07 10:16:00.343352+00
160	fyle	0025_auto_20230718_2027	2023-07-18 20:37:26.097468+00
161	fyle	0025_auto_20230720_1012	2023-08-03 14:22:12.599287+00
162	fyle	0026_auto_20230720_1014	2023-08-03 14:22:12.658375+00
163	fyle	0027_auto_20230801_0715	2023-08-03 14:22:12.71138+00
164	workspaces	0031_lastexportdetail_next_export	2023-08-03 14:22:12.731411+00
165	workspaces	0032_auto_20230810_0702	2023-08-10 08:02:48.464882+00
166	fyle	0028_remove_expensegroupsettings_import_card_credits	2023-10-19 10:40:26.050248+00
167	fyle_accounting_mappings	0023_auto_20230918_1316	2023-10-19 10:40:26.096281+00
168	fyle_accounting_mappings	0024_auto_20230922_0819	2023-10-19 10:40:26.190138+00
169	mappings	0015_importlog	2023-10-19 10:40:26.232859+00
170	fyle	0029_auto_20240130_0815	2024-01-30 08:16:09.353842+00
171	workspaces	0033_configuration_use_merchant_in_journal_line	2024-01-29 09:57:33.32801+00
172	django_q	0014_schedule_cluster	2024-02-12 12:17:55.492396+00
173	django_q	0015_alter_schedule_schedule_type	2024-02-12 12:17:55.497816+00
174	django_q	0016_schedule_intended_date_kwarg	2024-02-12 12:17:55.501763+00
175	django_q	0017_task_cluster_alter	2024-02-12 12:17:55.51124+00
176	tasks	0007_auto_20240305_0840	2024-03-05 08:41:17.389832+00
177	fyle_accounting_mappings	0025_expenseattributesdeletioncache	2024-04-01 07:56:25.110447+00
178	sage_intacct	0024_chargecardtransactionlineitem_user_defined_dimensions	2024-04-01 07:56:25.131511+00
179	fyle	0030_dependentfieldsetting_last_synced_at	2024-04-04 12:56:33.059637+00
180	sage_intacct	0025_costtype_is_imported	2024-04-04 12:56:33.07806+00
181	tasks	0008_error_repetition_count	2024-05-07 07:57:24.953894+00
182	tasks	0009_tasklog_supdoc_id	2024-05-20 09:36:04.874867+00
183	fyle	0031_expense_paid_on_fyle	2024-06-05 16:26:11.775475+00
184	workspaces	0034_configuration_is_journal_credit_billable	2024-06-19 07:16:22.418147+00
185	fyle	0032_auto_20240703_1818	2024-07-03 18:29:14.061756+00
186	workspaces	0035_configuration_auto_create_merchants_as_vendors	2024-07-26 17:26:19.583422+00
187	fyle	0033_expensegroup_export_url	2024-08-03 14:47:55.730073+00
188	sage_intacct	0026_billlineitem_allocation_id	2024-07-19 09:36:26.579359+00
189	sage_intacct	0027_journalentrylineitem_allocation_id	2024-07-26 11:27:56.709021+00
190	workspaces	0036_alter_configuration_is_journal_credit_billable	2024-08-06 11:33:56.808396+00
191	sage_intacct	0028_add_billable_field_to_cct	2024-09-05 19:30:23.212861+00
192	workspaces	0037_configuration_import_code_fields	2024-08-12 10:35:18.352466+00
193	fyle_accounting_mappings	0026_destinationattribute_code	2024-08-12 10:38:36.247956+00
194	workspaces	0038_alter_configuration_import_code_fields	2024-09-04 11:00:27.611651+00
195	sage_intacct	0029_auto_20240902_1511	2024-09-02 15:12:18.555335+00
196	fyle	0034_expense_is_posted_at_null	2024-11-18 04:59:52.076432+00
197	sage_intacct	0030_auto_20241112_0425	2024-11-18 04:59:52.138056+00
198	tasks	0010_alter_tasklog_expense_group	2024-11-18 04:59:52.206781+00
199	workspaces	0039_alter_configuration_change_accounting_period	2024-11-18 05:05:10.975057+00
200	fyle	0035_expense_masked_corporate_card_number	2024-11-20 02:49:32.481921+00
201	fyle_accounting_mappings	0027_alter_employeemapping_source_employee	2024-12-23 10:52:45.346752+00
202	workspaces	0040_auto_20241223_1050	2024-12-23 10:52:45.388875+00
203	fyle	0036_auto_20250108_0702	2025-01-08 07:37:35.954655+00
204	fyle_accounting_mappings	0028_auto_20241226_1030	2025-01-08 07:37:36.012387+00
205	mappings	0016_auto_20250108_0702	2025-01-08 07:37:36.082164+00
206	workspaces	0041_auto_20250108_0702	2025-01-08 07:37:36.448011+00
207	internal	0001_auto_generated_sql	2025-03-05 13:24:42.958137+00
208	internal	0002_auto_generated_sql	2025-03-05 13:24:42.960843+00
209	internal	0003_auto_generated_sql	2025-03-05 13:24:42.962442+00
210	internal	0004_auto_generated_sql	2025-03-05 13:24:42.964309+00
211	internal	0005_auto_generated_sql	2025-03-05 13:24:42.965784+00
212	internal	0006_auto_generated_sql	2025-03-05 13:24:42.967098+00
213	tasks	0011_tasklog_is_retired	2025-03-05 13:24:42.980154+00
214	fyle	0037_alter_dependentfieldsetting_cost_type_field_id_and_more	2025-03-10 14:19:51.122197+00
215	fyle	0038_dependentfieldsetting_is_cost_type_import_enabled	2025-03-10 14:19:51.131601+00
216	common_resources	0001_initial	2025-04-02 18:54:57.550584+00
217	workspaces	0042_remove_configuration_is_simplify_report_closure_enabled	2025-04-02 18:54:57.560272+00
218	fyle	0039_expense_imported_from	2025-04-07 15:36:06.377744+00
219	rabbitmq	0001_initial	2025-04-07 15:36:06.382304+00
220	rabbitmq	0002_alter_failedevent_error_traceback	2025-04-07 15:36:06.386096+00
221	rabbitmq	0003_alter_failedevent_created_at_and_more	2025-04-07 15:36:06.392208+00
222	tasks	0012_tasklog_triggered_by	2025-04-07 15:36:06.403887+00
223	fyle	0040_expense_expenses_account_ff34f0_idx_and_more	2025-04-10 16:29:32.548516+00
224	fyle	0041_alter_expense_imported_from	2025-04-10 16:29:32.566886+00
225	internal	0007_auto_generated_sql	2025-04-10 16:29:32.570096+00
226	internal	0008_auto_generated_sql	2025-04-10 16:29:32.573865+00
227	tasks	0013_alter_tasklog_triggered_by	2025-04-10 16:29:32.590805+00
228	internal	0009_auto_generate_sql	2025-04-10 19:15:23.717883+00
229	tasks	0013_error_mapping_error_expense_group_ids	2025-04-10 19:15:23.729634+00
230	tasks	0014_merge_20250410_1914	2025-04-10 19:15:23.73096+00
231	fyle_accounting_mappings	0029_expenseattributesdeletioncache_cost_center_ids_and_more	2025-04-24 16:15:00.272838+00
232	workspaces	0043_configuration_skip_accounting_export_summary_post	2025-04-24 16:15:00.283053+00
233	workspaces	0044_configuration_je_single_credit_line	2025-05-07 18:31:07.544615+00
234	sage_intacct	0031_costcode	2025-05-12 09:47:16.361962+00
235	rabbitmq	0004_failedevent_is_resolved	2025-05-21 17:02:59.151171+00
236	workspaces	0045_workspaceschedule_is_real_time_export_enabled	2025-05-21 17:05:12.778782+00
237	workspaces	0045_sageintacctcredential_is_expired	2025-06-03 13:10:42.732351+00
238	workspaces	0046_merge_20250603_1307	2025-06-03 13:10:42.733986+00
239	fyle_integrations_imports	0001_initial	2025-06-03 09:13:14.987582+00
240	workspaces	0047_configuration_top_level_memo_structure	2025-06-03 13:10:42.735621+00
241	fyle_accounting_mappings	0030_expenseattributesdeletioncache_updated_at	2025-06-17 11:21:51.697718+00
242	internal	0010_auto_generated_sql	2025-06-17 11:21:51.706446+00
243	internal	0011_auto_generated_sql	2025-07-31 11:52:06.408889+00
244	internal	0012_auto_generated_sql	2025-07-31 11:52:06.419581+00
245	internal	0013_auto_generated_sql	2025-07-31 11:52:06.434321+00
246	workspaces	0048_lastexportdetail_unmapped_card_count	2025-07-31 11:52:06.481827+00
247	tasks	0015_tasklog_re_attempt_export	2025-08-05 08:54:20.464377+00
248	workspaces	0049_featureconfig	2025-09-12 05:48:50.923799+00
249	workspaces	0050_featureconfig_import_via_rabbitmq_and_more	2025-09-12 05:48:50.948371+00
250	internal	0014_auto_generated_sql	2025-10-10 09:38:10.294351+00
251	internal	0015_auto_generated_sql	2025-10-10 09:38:10.300549+00
252	internal	0016_auto_generated_sql	2025-10-10 09:38:10.303861+00
253	internal	0017_auto_generated_sql	2025-10-10 09:38:10.306449+00
254	internal	0018_auto_generated_sql	2025-10-10 09:38:10.308257+00
255	internal	0019_auto_generated_sql	2025-10-10 09:38:10.32163+00
256	workspaces	0051_alter_featureconfig_export_via_rabbitmq_and_more	2025-10-10 09:38:10.360728+00
257	fyle_accounting_mappings	0031_fylesynctimestamp	2025-10-21 09:33:37.853529+00
258	workspaces	0052_featureconfig_fyle_webhook_sync_enabled	2025-10-21 09:33:37.868431+00
259	internal	0020_auto_generated_sql	2025-10-29 16:25:12.991416+00
260	internal	0021_auto_generated_sql	2025-10-31 06:45:42.642859+00
261	internal	0022_auto_generated_sql	2025-10-31 06:45:42.64653+00
262	workspaces	0053_sageintacctcredential_refresh_token	2025-11-10 07:51:10.660732+00
263	fyle	0042_expense_expenses_workspa_ad984e_idx	2025-11-13 11:11:43.58984+00
264	workspaces	0054_alter_featureconfig_fyle_webhook_sync_enabled	2025-11-13 11:11:43.630578+00
265	internal	0023_auto_generated_sql	2025-11-13 11:11:43.640549+00
266	workspaces	0055_featureconfig_migrated_to_rest_api	2025-11-13 11:11:43.675733+00
267	workspaces	0056_sageintacctcredential_access_token_and_more	2025-11-13 18:29:54.777978+00
268	workspaces	0057_intacctsyncedtimestamp	2025-11-21 18:32:09.960426+00
269	internal	0024_auto_generated_sql	2025-11-21 18:32:09.964181+00
270	internal	0025_auto_generated_sql	2025-11-21 18:32:09.969995+00
271	sage_intacct	0032_sageintacctattributescount	2025-11-21 18:32:10.00795+00
272	internal	0026_auto_generated_sql	2025-11-25 07:37:50.264835+00
273	tasks	0016_tasklog_is_attachment_upload_failed	2025-11-25 07:37:50.286441+00
\.


--
-- Data for Name: django_q_ormq; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_q_ormq (id, key, payload, lock) FROM stdin;
\.


--
-- Data for Name: django_q_schedule; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_q_schedule (id, func, hook, args, kwargs, schedule_type, repeats, next_run, task, name, minutes, cron, cluster, intended_date_kwarg) FROM stdin;
5	apps.mappings.tasks.auto_create_project_mappings	\N	1	\N	I	-5	2022-09-30 08:46:24.989603+00	54ab7ab7396741eea35de26e72b73c18	\N	1440	\N	\N	\N
3	apps.mappings.tasks.auto_create_tax_codes_mappings	\N	1	\N	I	-5	2022-09-30 08:46:25.03867+00	72495cee26334ea9ad64b337f757c4a6	\N	1440	\N	\N	\N
4	apps.mappings.tasks.auto_create_vendors_as_merchants	\N	1	\N	I	-5	2022-09-30 08:46:25.0608+00	3bdcf280bd6c42a197ad24f932ce39c7	\N	1440	\N	\N	\N
93	apps.internal.tasks.re_export_stuck_exports	\N	\N	\N	I	-1	2025-03-05 13:25:42.96495+00	\N	\N	60	\N	\N	\N
94	apps.internal.tasks.pause_and_resume_export_schedules	\N	\N	\N	I	-1	2025-04-10 16:39:32.568532+00	\N	\N	1440	\N	\N	\N
95	apps.mappings.tasks.auto_map_accounting_fields	\N	1	\N	I	-1	2022-09-30 08:46:24.994645+00	\N	\N	1440	\N	\N	\N
96	apps.sage_intacct.queue.trigger_sync_payments	\N	1	\N	I	-1	2022-09-30 08:47:19.647275+00	\N	\N	1440	\N	\N	\N
\.


--
-- Data for Name: django_q_task; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_q_task (name, func, hook, args, kwargs, result, started, stopped, success, id, "group", attempt_count, cluster) FROM stdin;
asparagus-single-jersey-blue	apps.mappings.tasks.auto_create_tax_codes_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:40:13.062302+00	2022-09-20 08:40:15.683139+00	t	802d2482ae304c14a0b445386e266838	3	1	\N
friend-vegan-shade-zulu	apps.mappings.tasks.async_auto_map_employees	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:40:13.015775+00	2022-09-20 08:40:23.134177+00	t	325cb28cdceb4499be096c1fdb53b5c2	2	1	import
low-sad-river-yellow	apps.mappings.tasks.auto_create_vendors_as_merchants	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:40:13.122168+00	2022-09-20 08:40:24.046441+00	t	51f89542d0684e48b1a7af008d26cc9a	4	1	\N
missouri-winner-utah-yankee	apps.mappings.tasks.auto_create_project_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:40:13.167858+00	2022-09-20 08:40:26.030092+00	t	59f22b0e0d7947c5924b2d1dedaab902	5	1	\N
robert-july-kansas-monkey	apps.mappings.tasks.auto_create_category_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	gARdlC4=	2022-09-20 08:40:12.962536+00	2022-09-20 08:40:39.053201+00	t	b78956d25b524327a759f2631eace0c3	1	1	\N
sodium-alabama-charlie-six	apps.mappings.tasks.auto_create_tax_codes_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:47:07.568062+00	2022-09-20 08:47:09.466315+00	t	8ed8aa314cf54df5ae67917d12e1c3f8	3	1	\N
idaho-august-bakerloo-sweet	apps.mappings.tasks.auto_create_project_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:47:07.508948+00	2022-09-20 08:47:16.31791+00	t	3728e698bc884e77a6571dfd037b8827	5	1	\N
dakota-pennsylvania-michigan-oranges	apps.mappings.tasks.auto_create_vendors_as_merchants	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:47:07.593487+00	2022-09-20 08:47:16.412242+00	t	a7bd586d911648619bf727c2def3119a	4	1	\N
london-item-idaho-bacon	apps.mappings.tasks.async_auto_map_employees	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:47:07.540279+00	2022-09-20 08:47:16.427793+00	t	3cffad1235aa46b1b8ba30535aa7dc31	2	1	import
eight-michigan-virginia-mobile	apps.sage_intacct.tasks.create_ap_payment	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:47:49.746201+00	2022-09-20 08:47:52.196922+00	t	ef431c8b04584d98bf1cedbe816fb1d0	6	1	\N
india-texas-beryllium-social	apps.fyle.tasks.create_expense_groups	\N	gASVUwIAAAAAAABLAV2UKIwIUEVSU09OQUyUjANDQ0OUZYwVZGphbmdvLmRiLm1vZGVscy5iYXNllIwObW9kZWxfdW5waWNrbGWUk5SMBXRhc2tzlIwHVGFza0xvZ5SGlIWUUpR9lCiMBl9zdGF0ZZRoA4wKTW9kZWxTdGF0ZZSTlCmBlH2UKIwMZmllbGRzX2NhY2hllH2UjAJkYpSMB2RlZmF1bHSUjAZhZGRpbmeUiXVijAJpZJRLAYwMd29ya3NwYWNlX2lklEsBjAR0eXBllIwRRkVUQ0hJTkdfRVhQRU5TRVOUjAd0YXNrX2lklE6MEGV4cGVuc2VfZ3JvdXBfaWSUTowHYmlsbF9pZJROjBFleHBlbnNlX3JlcG9ydF9pZJROjBpjaGFyZ2VfY2FyZF90cmFuc2FjdGlvbl9pZJROjBBqb3VybmFsX2VudHJ5X2lklE6MDWFwX3BheW1lbnRfaWSUTowdc2FnZV9pbnRhY2N0X3JlaW1idXJzZW1lbnRfaWSUTowGc3RhdHVzlIwIQ09NUExFVEWUjAZkZXRhaWyUfZRoFIwNZGVmYXVsdCB2YWx1ZZRzjBNzYWdlX2ludGFjY3RfZXJyb3JzlE6MCmNyZWF0ZWRfYXSUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH5gkUCDAVAAJ2lIwEcHl0epSMBF9VVEOUk5QpUpSGlFKUjAp1cGRhdGVkX2F0lGgrQwoH5gkUCDAVC8VglGgwhpRSlIwPX2RqYW5nb192ZXJzaW9ulIwGMy4xLjE0lHVih5Qu	gAR9lC4=	\N	2022-09-20 08:48:21.025429+00	2022-09-20 08:48:21.779769+00	t	f8b7361a9d5b4c5796d41344c8836dea	\N	1	\N
romeo-fish-twelve-vegan	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:48:35.736509+00	2022-09-20 08:48:37.363333+00	t	faa12acd7fc84bba942fe6bf33209b62	7f54e4e107e54f84851873e36f5ab041	1	\N
seventeen-michigan-magnesium-east	apps.sage_intacct.tasks.create_bill	\N	gASV7QEAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBmFkZGluZ5SJjAJkYpSMB2RlZmF1bHSUdWKMAmlklEsBjAtmdW5kX3NvdXJjZZSMCFBFUlNPTkFMlIwMd29ya3NwYWNlX2lklEsBjAtkZXNjcmlwdGlvbpR9lCiMCXJlcG9ydF9pZJSMDHJwRVpHcVZDeVd4UZSMC2Z1bmRfc291cmNllIwIUEVSU09OQUyUjAxjbGFpbV9udW1iZXKUjA5DLzIwMjIvMDkvUi8yMZSMDmVtcGxveWVlX2VtYWlslIwQYXNod2luLnRAZnlsZS5pbpR1jApjcmVhdGVkX2F0lIwIZGF0ZXRpbWWUjAhkYXRldGltZZSTlEMKB+YJFAgwFQut15SMBHB5dHqUjARfVVRDlJOUKVKUhpRSlIwLZXhwb3J0ZWRfYXSUTowKdXBkYXRlZF9hdJRoJEMKB+YJFAgwFQuuBZRoKYaUUpSMD19kamFuZ29fdmVyc2lvbpSMBjMuMS4xNJR1YksChpQu	gAR9lC4=	\N	2022-09-20 08:48:37.377162+00	2022-09-20 08:48:40.023104+00	t	b6054434b7f6438bad8d6dcdc5c3043a	7f54e4e107e54f84851873e36f5ab041	1	\N
undress-pip-two-lima	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:49:12.074551+00	2022-09-20 08:49:13.746885+00	t	ca9e00b2d0484c7bbb8962b46bd1c102	01f953e8bcfb4b3d8f539d84a14940fd	1	\N
oven-helium-vermont-alabama	apps.sage_intacct.tasks.create_bill	\N	gASVXgMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQoaAloCymBlH2UKIwCZGKUjAdkZWZhdWx0lGgOfZSMDWV4cGVuc2VfZ3JvdXCUaAdzjAZhZGRpbmeUiXVijAJpZJRLAYwQZXhwZW5zZV9ncm91cF9pZJRLAYwJdmVuZG9yX2lklIwGQXNod2lulIwLZGVzY3JpcHRpb26UfZQojAlyZXBvcnRfaWSUjAxycEVaR3FWQ3lXeFGUjAtmdW5kX3NvdXJjZZSMCFBFUlNPTkFMlIwMY2xhaW1fbnVtYmVylIwOQy8yMDIyLzA5L1IvMjGUjA5lbXBsb3llZV9lbWFpbJSMEGFzaHdpbi50QGZ5bGUuaW6UdYwEbWVtb5SMJVJlaW1idXJzYWJsZSBleHBlbnNlIC0gQy8yMDIyLzA5L1IvMjGUjAhjdXJyZW5jeZSMA1VTRJSMCXN1cGRvY19pZJROjBB0cmFuc2FjdGlvbl9kYXRllIwTMjAyMi0wOS0yMFQwODo0OToxNpSMDnBheW1lbnRfc3luY2VklImMFHBhaWRfb25fc2FnZV9pbnRhY2N0lImMCmNyZWF0ZWRfYXSUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH5gkUCDEQBfyplIwEcHl0epSMBF9VVEOUk5QpUpSGlFKUjAp1cGRhdGVkX2F0lGg4QwoH5gkUCDEQBgIslGg9hpRSlIwPX2RqYW5nb192ZXJzaW9ulIwGMy4xLjE0lHVic2gdiWgZjAdkZWZhdWx0lHViaB5LAYwLZnVuZF9zb3VyY2WUjAhQRVJTT05BTJSMDHdvcmtzcGFjZV9pZJRLAWgiaCNoNWg4QwoH5gkUCDAVC63XlGg9hpRSlIwLZXhwb3J0ZWRfYXSUTmhAaDhDCgfmCRQIMBULrgWUaD2GlFKUjA9fZGphbmdvX3ZlcnNpb26UaEV1YksChpQu	gAR9lC4=	\N	2022-09-20 08:49:13.750365+00	2022-09-20 08:49:19.102546+00	t	6787d29bbe924030afc456d1a4d20473	01f953e8bcfb4b3d8f539d84a14940fd	1	\N
vegan-nuts-ten-salami	apps.fyle.tasks.create_expense_groups	\N	gASVWwIAAAAAAABLAV2UKIwIUEVSU09OQUyUjANDQ0OUZYwVZGphbmdvLmRiLm1vZGVscy5iYXNllIwObW9kZWxfdW5waWNrbGWUk5SMBXRhc2tzlIwHVGFza0xvZ5SGlIWUUpR9lCiMBl9zdGF0ZZRoA4wKTW9kZWxTdGF0ZZSTlCmBlH2UKIwMZmllbGRzX2NhY2hllH2UjAZhZGRpbmeUiYwCZGKUjAdkZWZhdWx0lHVijAJpZJRLAYwMd29ya3NwYWNlX2lklEsBjAR0eXBllIwRRkVUQ0hJTkdfRVhQRU5TRVOUjAd0YXNrX2lklE6MEGV4cGVuc2VfZ3JvdXBfaWSUTowHYmlsbF9pZJROjBFleHBlbnNlX3JlcG9ydF9pZJROjBpjaGFyZ2VfY2FyZF90cmFuc2FjdGlvbl9pZJROjBBqb3VybmFsX2VudHJ5X2lklE6MDWFwX3BheW1lbnRfaWSUTowdc2FnZV9pbnRhY2N0X3JlaW1idXJzZW1lbnRfaWSUTowGc3RhdHVzlIwIQ09NUExFVEWUjAZkZXRhaWyUfZSMB2RlZmF1bHSUjA1kZWZhdWx0IHZhbHVllHOME3NhZ2VfaW50YWNjdF9lcnJvcnOUTowKY3JlYXRlZF9hdJSMCGRhdGV0aW1llIwIZGF0ZXRpbWWUk5RDCgfmCRQIMBUAAnaUjARweXR6lIwEX1VUQ5STlClSlIaUUpSMCnVwZGF0ZWRfYXSUaCxDCgfmCRQIMxsKOP6UaDGGlFKUjA9fZGphbmdvX3ZlcnNpb26UjAYzLjEuMTSUdWKHlC4=	gAR9lC4=	\N	2022-09-20 08:51:26.412218+00	2022-09-20 08:51:27.680767+00	t	20f78db05a22479fa0fa66e6348de9ef	\N	1	\N
aspen-king-football-july	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:51:33.400089+00	2022-09-20 08:51:34.085655+00	t	1eb88d2796a44c0c892ab058956351ca	03e74dbb40794336811835d3bbd78800	1	\N
fanta-zebra-red-failed	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:51:33.202866+00	2022-09-20 08:51:34.095834+00	t	f06271a131164f96beb945fa139dd31c	9850400d7ae1446498d1cce14bdea90a	1	\N
kansas-missouri-high-ten	apps.sage_intacct.tasks.create_ap_payment	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 11:20:39.441124+00	2022-09-28 11:20:41.346546+00	t	446b5f1ff9644556a81230d709ee84b9	6	1	\N
undress-xray-enemy-paris	apps.mappings.tasks.async_auto_map_employees	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 11:20:39.412662+00	2022-09-28 11:20:46.951256+00	t	1eb4c884d91543749bf8306cfbe1a711	2	1	import
aspen-april-mirror-alaska	apps.mappings.tasks.auto_create_vendors_as_merchants	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 11:20:39.430756+00	2022-09-28 11:20:47.741487+00	t	8c3b10abff37448ba38bcf6b1d635e23	4	1	\N
ten-monkey-sodium-uranus	apps.mappings.tasks.auto_create_project_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 11:20:39.389393+00	2022-09-28 11:20:48.080556+00	t	a86d100ffd8945a089bd639a1c1a917f	5	1	\N
delta-california-apart-sierra	apps.sage_intacct.tasks.create_bill	\N	gASVhQMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQoaAloCymBlH2UKIwCZGKUjAdkZWZhdWx0lGgOfZSMDWV4cGVuc2VfZ3JvdXCUaAdzjAZhZGRpbmeUiXVijAJpZJRLAowQZXhwZW5zZV9ncm91cF9pZJRLAowJdmVuZG9yX2lklIwFMjAwNDOUjAtkZXNjcmlwdGlvbpR9lCiMCXJlcG9ydF9pZJSMDHJwU1RZTzhBZlVWQZSMCmV4cGVuc2VfaWSUjAx0eENxTHFzRW5BamaUjAtmdW5kX3NvdXJjZZSMA0NDQ5SMDGNsYWltX251bWJlcpSMDkMvMjAyMi8wOS9SLzIylIwOZW1wbG95ZWVfZW1haWyUjBBhc2h3aW4udEBmeWxlLmlulHWMBG1lbW+UjDtDb3Jwb3JhdGUgQ3JlZGl0IENhcmQgZXhwZW5zZSAtIEMvMjAyMi8wOS9SLzIyIC0gMjAvMDkvMjAyMpSMCGN1cnJlbmN5lIwDVVNElIwJc3VwZG9jX2lklE6MEHRyYW5zYWN0aW9uX2RhdGWUjBMyMDIyLTA5LTIwVDA4OjUxOjM2lIwOcGF5bWVudF9zeW5jZWSUiYwUcGFpZF9vbl9zYWdlX2ludGFjY3SUiYwKY3JlYXRlZF9hdJSMCGRhdGV0aW1llIwIZGF0ZXRpbWWUk5RDCgfmCRQIMyQCuRyUjARweXR6lIwEX1VUQ5STlClSlIaUUpSMCnVwZGF0ZWRfYXSUaDpDCgfmCRQIMyQCuUeUaD+GlFKUjA9fZGphbmdvX3ZlcnNpb26UjAYzLjEuMTSUdWJzaB2JaBmMB2RlZmF1bHSUdWJoHksCjAtmdW5kX3NvdXJjZZSMA0NDQ5SMDHdvcmtzcGFjZV9pZJRLAWgiaCNoN2g6QwoH5gkUCDMbCe9rlGg/hpRSlIwLZXhwb3J0ZWRfYXSUTmhCaDpDCgfmCRQIMxsJ75+UaD+GlFKUjA9fZGphbmdvX3ZlcnNpb26UaEd1YksDhpQu	gAR9lC4=	\N	2022-09-20 08:51:34.094557+00	2022-09-20 08:51:38.08379+00	t	05d919f7e8fe4b4396358623b7c59423	03e74dbb40794336811835d3bbd78800	1	\N
lake-quebec-beryllium-yellow	apps.sage_intacct.tasks.create_bill	\N	gASVXgMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQoaAloCymBlH2UKIwCZGKUjAdkZWZhdWx0lGgOfZSMDWV4cGVuc2VfZ3JvdXCUaAdzjAZhZGRpbmeUiXVijAJpZJRLA4wQZXhwZW5zZV9ncm91cF9pZJRLAYwJdmVuZG9yX2lklIwGQXNod2lulIwLZGVzY3JpcHRpb26UfZQojAlyZXBvcnRfaWSUjAxycEVaR3FWQ3lXeFGUjAtmdW5kX3NvdXJjZZSMCFBFUlNPTkFMlIwMY2xhaW1fbnVtYmVylIwOQy8yMDIyLzA5L1IvMjGUjA5lbXBsb3llZV9lbWFpbJSMEGFzaHdpbi50QGZ5bGUuaW6UdYwEbWVtb5SMJVJlaW1idXJzYWJsZSBleHBlbnNlIC0gQy8yMDIyLzA5L1IvMjGUjAhjdXJyZW5jeZSMA1VTRJSMCXN1cGRvY19pZJROjBB0cmFuc2FjdGlvbl9kYXRllIwTMjAyMi0wOS0yMFQwODo1MTozNpSMDnBheW1lbnRfc3luY2VklImMFHBhaWRfb25fc2FnZV9pbnRhY2N0lImMCmNyZWF0ZWRfYXSUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH5gkUCDMkDOlTlIwEcHl0epSMBF9VVEOUk5QpUpSGlFKUjAp1cGRhdGVkX2F0lGg4QwoH5gkUCDMkDOl1lGg9hpRSlIwPX2RqYW5nb192ZXJzaW9ulIwGMy4xLjE0lHVic2gdiWgZjAdkZWZhdWx0lHViaB5LAYwLZnVuZF9zb3VyY2WUjAhQRVJTT05BTJSMDHdvcmtzcGFjZV9pZJRLAWgiaCNoNWg4QwoH5gkUCDAVC63XlGg9hpRSlIwLZXhwb3J0ZWRfYXSUTmhAaDhDCgfmCRQIMBULrgWUaD2GlFKUjA9fZGphbmdvX3ZlcnNpb26UaEV1YksChpQu	gAR9lC4=	\N	2022-09-20 08:51:34.197425+00	2022-09-20 08:51:38.764149+00	t	7b8631b94a25409a9ec48ac51ca41356	9850400d7ae1446498d1cce14bdea90a	1	\N
foxtrot-papa-gee-carbon	apps.fyle.tasks.create_expense_groups	\N	gASVWwIAAAAAAABLAV2UKIwIUEVSU09OQUyUjANDQ0OUZYwVZGphbmdvLmRiLm1vZGVscy5iYXNllIwObW9kZWxfdW5waWNrbGWUk5SMBXRhc2tzlIwHVGFza0xvZ5SGlIWUUpR9lCiMBl9zdGF0ZZRoA4wKTW9kZWxTdGF0ZZSTlCmBlH2UKIwMZmllbGRzX2NhY2hllH2UjAZhZGRpbmeUiYwCZGKUjAdkZWZhdWx0lHVijAJpZJRLAYwMd29ya3NwYWNlX2lklEsBjAR0eXBllIwRRkVUQ0hJTkdfRVhQRU5TRVOUjAd0YXNrX2lklE6MEGV4cGVuc2VfZ3JvdXBfaWSUTowHYmlsbF9pZJROjBFleHBlbnNlX3JlcG9ydF9pZJROjBpjaGFyZ2VfY2FyZF90cmFuc2FjdGlvbl9pZJROjBBqb3VybmFsX2VudHJ5X2lklE6MDWFwX3BheW1lbnRfaWSUTowdc2FnZV9pbnRhY2N0X3JlaW1idXJzZW1lbnRfaWSUTowGc3RhdHVzlIwIQ09NUExFVEWUjAZkZXRhaWyUfZSMB2RlZmF1bHSUjA1kZWZhdWx0IHZhbHVllHOME3NhZ2VfaW50YWNjdF9lcnJvcnOUTowKY3JlYXRlZF9hdJSMCGRhdGV0aW1llIwIZGF0ZXRpbWWUk5RDCgfmCRQIMBUAAnaUjARweXR6lIwEX1VUQ5STlClSlIaUUpSMCnVwZGF0ZWRfYXSUaCxDCgfmCRQIODICTFaUaDGGlFKUjA9fZGphbmdvX3ZlcnNpb26UjAYzLjEuMTSUdWKHlC4=	gAR9lC4=	\N	2022-09-20 08:56:49.260438+00	2022-09-20 08:56:50.158376+00	t	2313225c5df34247a6c12510256abcec	\N	1	\N
queen-nuts-edward-sixteen	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:57:02.275682+00	2022-09-20 08:57:03.087054+00	t	12f9623f65e44564b1ff2a5ebfdb0aa7	02277d4db84343239a89541cec3c7b82	1	\N
double-apart-mirror-stream	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-20 08:57:02.332442+00	2022-09-20 08:57:03.186795+00	t	9789012adeb04f279f212b19b7df8b36	acc928ba6bf4400c8268331a29189313	1	\N
uranus-december-orange-ink	apps.sage_intacct.tasks.create_bill	\N	gASVXgMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQoaAloCymBlH2UKIwCZGKUjAdkZWZhdWx0lGgOfZSMDWV4cGVuc2VfZ3JvdXCUaAdzjAZhZGRpbmeUiXVijAJpZJRLBIwQZXhwZW5zZV9ncm91cF9pZJRLAYwJdmVuZG9yX2lklIwGQXNod2lulIwLZGVzY3JpcHRpb26UfZQojAlyZXBvcnRfaWSUjAxycEVaR3FWQ3lXeFGUjAtmdW5kX3NvdXJjZZSMCFBFUlNPTkFMlIwMY2xhaW1fbnVtYmVylIwOQy8yMDIyLzA5L1IvMjGUjA5lbXBsb3llZV9lbWFpbJSMEGFzaHdpbi50QGZ5bGUuaW6UdYwEbWVtb5SMJVJlaW1idXJzYWJsZSBleHBlbnNlIC0gQy8yMDIyLzA5L1IvMjGUjAhjdXJyZW5jeZSMA1VTRJSMCXN1cGRvY19pZJROjBB0cmFuc2FjdGlvbl9kYXRllIwTMjAyMi0wOS0yMFQwODo1NzowNZSMDnBheW1lbnRfc3luY2VklImMFHBhaWRfb25fc2FnZV9pbnRhY2N0lImMCmNyZWF0ZWRfYXSUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH5gkUCDkFBPS8lIwEcHl0epSMBF9VVEOUk5QpUpSGlFKUjAp1cGRhdGVkX2F0lGg4QwoH5gkUCDkFBPTnlGg9hpRSlIwPX2RqYW5nb192ZXJzaW9ulIwGMy4xLjE0lHVic2gdiWgZjAdkZWZhdWx0lHViaB5LAYwLZnVuZF9zb3VyY2WUjAhQRVJTT05BTJSMDHdvcmtzcGFjZV9pZJRLAWgiaCNoNWg4QwoH5gkUCDAVC63XlGg9hpRSlIwLZXhwb3J0ZWRfYXSUTmhAaDhDCgfmCRQIMBULrgWUaD2GlFKUjA9fZGphbmdvX3ZlcnNpb26UaEV1YksChpQu	gAR9lC4=	\N	2022-09-20 08:57:03.089187+00	2022-09-20 08:57:06.870381+00	t	8bd9ce74882d4adf958f0cb39d68e777	02277d4db84343239a89541cec3c7b82	1	\N
nebraska-leopard-romeo-pennsylvania	apps.sage_intacct.tasks.create_bill	\N	gASVhQMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQoaAloCymBlH2UKIwCZGKUjAdkZWZhdWx0lGgOfZSMDWV4cGVuc2VfZ3JvdXCUaAdzjAZhZGRpbmeUiXVijAJpZJRLBYwQZXhwZW5zZV9ncm91cF9pZJRLAowJdmVuZG9yX2lklIwFMjAwNDOUjAtkZXNjcmlwdGlvbpR9lCiMCXJlcG9ydF9pZJSMDHJwU1RZTzhBZlVWQZSMCmV4cGVuc2VfaWSUjAx0eENxTHFzRW5BamaUjAtmdW5kX3NvdXJjZZSMA0NDQ5SMDGNsYWltX251bWJlcpSMDkMvMjAyMi8wOS9SLzIylIwOZW1wbG95ZWVfZW1haWyUjBBhc2h3aW4udEBmeWxlLmlulHWMBG1lbW+UjDtDb3Jwb3JhdGUgQ3JlZGl0IENhcmQgZXhwZW5zZSAtIEMvMjAyMi8wOS9SLzIyIC0gMjAvMDkvMjAyMpSMCGN1cnJlbmN5lIwDVVNElIwJc3VwZG9jX2lklE6MEHRyYW5zYWN0aW9uX2RhdGWUjBMyMDIyLTA5LTIwVDA4OjU3OjA1lIwOcGF5bWVudF9zeW5jZWSUiYwUcGFpZF9vbl9zYWdlX2ludGFjY3SUiYwKY3JlYXRlZF9hdJSMCGRhdGV0aW1llIwIZGF0ZXRpbWWUk5RDCgfmCRQIOQUNJJeUjARweXR6lIwEX1VUQ5STlClSlIaUUpSMCnVwZGF0ZWRfYXSUaDpDCgfmCRQIOQUNJLqUaD+GlFKUjA9fZGphbmdvX3ZlcnNpb26UjAYzLjEuMTSUdWJzaB2JaBmMB2RlZmF1bHSUdWJoHksCjAtmdW5kX3NvdXJjZZSMA0NDQ5SMDHdvcmtzcGFjZV9pZJRLAWgiaCNoN2g6QwoH5gkUCDMbCe9rlGg/hpRSlIwLZXhwb3J0ZWRfYXSUTmhCaDpDCgfmCRQIMxsJ75+UaD+GlFKUjA9fZGphbmdvX3ZlcnNpb26UaEd1YksDhpQu	gAR9lC4=	\N	2022-09-20 08:57:03.248067+00	2022-09-20 08:57:07.929346+00	t	5fec2004d21d4dfab405e6ebb3e557af	acc928ba6bf4400c8268331a29189313	1	\N
utah-uncle-king-orange	apps.sage_intacct.tasks.create_bill	\N	gASV/wEAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBmFkZGluZ5SJjAJkYpSMB2RlZmF1bHSUdWKMAmlklEsDjAtmdW5kX3NvdXJjZZSMA0NDQ5SMDHdvcmtzcGFjZV9pZJRLAYwLZGVzY3JpcHRpb26UfZQojAlyZXBvcnRfaWSUjAxycEJmNWlicVVUNkKUjApleHBlbnNlX2lklIwMdHhUSGZFUFdPRU9wlIwLZnVuZF9zb3VyY2WUjANDQ0OUjAxjbGFpbV9udW1iZXKUjA5DLzIwMjIvMDkvUi8yM5SMDmVtcGxveWVlX2VtYWlslIwQYXNod2luLnRAZnlsZS5pbpR1jApjcmVhdGVkX2F0lIwIZGF0ZXRpbWWUjAhkYXRldGltZZSTlEMKB+YJFAg4MgI/TJSMBHB5dHqUjARfVVRDlJOUKVKUhpRSlIwLZXhwb3J0ZWRfYXSUTowKdXBkYXRlZF9hdJRoJkMKB+YJFAg4MgI/fJRoK4aUUpSMD19kamFuZ29fdmVyc2lvbpSMBjMuMS4xNJR1YksEhpQu	gAR9lC4=	\N	2022-09-20 08:57:07.930662+00	2022-09-20 08:57:10.250024+00	t	092706c1f82f42708b17f7190f0558f7	acc928ba6bf4400c8268331a29189313	1	\N
edward-uncle-july-east	apps.mappings.tasks.auto_create_tax_codes_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 11:20:39.419171+00	2022-09-28 11:20:40.74238+00	t	6c59343bf7f04fada99d065f6361c3f9	3	1	\N
yellow-montana-paris-utah	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 11:56:27.975206+00	2022-09-28 11:56:29.172725+00	t	93f23aa67d394197925f59388b487a50	cfdf480bf3fc455685e5b8b3a11977d0	1	\N
blue-king-single-hawaii	apps.fyle.tasks.sync_reimbursements	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-28 11:56:28.025405+00	2022-09-28 11:56:29.204256+00	t	629646aa0a0e4137ba09ec99581affe6	8411b791379d452c90d082aa158668a4	1	\N
yankee-eleven-fanta-lamp	apps.sage_intacct.tasks.create_bill	\N	gASVsQMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQojAZfc3RhdGWUaAspgZR9lCiMAmRilIwHZGVmYXVsdJRoDn2UjA1leHBlbnNlX2dyb3VwlGgHc4wGYWRkaW5nlIl1YowCaWSUSweMEGV4cGVuc2VfZ3JvdXBfaWSUSwKMCXZlbmRvcl9pZJSMBTIwMDQzlIwLZGVzY3JpcHRpb26UfZQojAlyZXBvcnRfaWSUjAxycFNUWU84QWZVVkGUjApleHBlbnNlX2lklIwMdHhDcUxxc0VuQWpmlIwLZnVuZF9zb3VyY2WUjANDQ0OUjAxjbGFpbV9udW1iZXKUjA5DLzIwMjIvMDkvUi8yMpSMDmVtcGxveWVlX2VtYWlslIwQYXNod2luLnRAZnlsZS5pbpR1jARtZW1vlIw7Q29ycG9yYXRlIENyZWRpdCBDYXJkIGV4cGVuc2UgLSBDLzIwMjIvMDkvUi8yMiAtIDI4LzA5LzIwMjKUjAhjdXJyZW5jeZSMA1VTRJSMCXN1cGRvY19pZJROjBB0cmFuc2FjdGlvbl9kYXRllIwTMjAyMi0wOS0yOFQxMTo1NjozMZSMDnBheW1lbnRfc3luY2VklImMFHBhaWRfb25fc2FnZV9pbnRhY2N0lImMCmNyZWF0ZWRfYXSUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH5gkcCzgfDOlBlIwEcHl0epSMBF9VVEOUk5QpUpSGlFKUjAp1cGRhdGVkX2F0lGg7QwoH5gkcCzgfDOl1lGhAhpRSlIwPX2RqYW5nb192ZXJzaW9ulIwGMy4xLjE0lHVic2geiWgajAdkZWZhdWx0lHVijAJpZJRLAowLZnVuZF9zb3VyY2WUjANDQ0OUjAx3b3Jrc3BhY2VfaWSUSwGMC2Rlc2NyaXB0aW9ulGgkjApjcmVhdGVkX2F0lGg7QwoH5gkUCDMbCe9rlGhAhpRSlIwLZXhwb3J0ZWRfYXSUTowKdXBkYXRlZF9hdJRoO0MKB+YJFAgzGwnvn5RoQIaUUpSMD19kamFuZ29fdmVyc2lvbpRoSHViSwOGlC4=	gAR9lC4=	\N	2022-09-28 11:56:29.46252+00	2022-09-28 11:56:33.943154+00	t	f1f296693ae042a5b8933158e4529c5c	8411b791379d452c90d082aa158668a4	1	\N
virginia-tango-three-connecticut	apps.sage_intacct.tasks.create_bill	\N	gASVigMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQojAZfc3RhdGWUaAspgZR9lCiMAmRilIwHZGVmYXVsdJRoDn2UjA1leHBlbnNlX2dyb3VwlGgHc4wGYWRkaW5nlIl1YowCaWSUSwaMEGV4cGVuc2VfZ3JvdXBfaWSUSwGMCXZlbmRvcl9pZJSMBkFzaHdpbpSMC2Rlc2NyaXB0aW9ulH2UKIwJcmVwb3J0X2lklIwMcnBFWkdxVkN5V3hRlIwLZnVuZF9zb3VyY2WUjAhQRVJTT05BTJSMDGNsYWltX251bWJlcpSMDkMvMjAyMi8wOS9SLzIxlIwOZW1wbG95ZWVfZW1haWyUjBBhc2h3aW4udEBmeWxlLmlulHWMBG1lbW+UjCVSZWltYnVyc2FibGUgZXhwZW5zZSAtIEMvMjAyMi8wOS9SLzIxlIwIY3VycmVuY3mUjANVU0SUjAlzdXBkb2NfaWSUTowQdHJhbnNhY3Rpb25fZGF0ZZSMEzIwMjItMDktMjhUMTE6NTY6MzGUjA5wYXltZW50X3N5bmNlZJSJjBRwYWlkX29uX3NhZ2VfaW50YWNjdJSJjApjcmVhdGVkX2F0lIwIZGF0ZXRpbWWUjAhkYXRldGltZZSTlEMKB+YJHAs4Hwt0spSMBHB5dHqUjARfVVRDlJOUKVKUhpRSlIwKdXBkYXRlZF9hdJRoOUMKB+YJHAs4Hwt1EZRoPoaUUpSMD19kamFuZ29fdmVyc2lvbpSMBjMuMS4xNJR1YnNoHoloGowHZGVmYXVsdJR1YowCaWSUSwGMC2Z1bmRfc291cmNllIwIUEVSU09OQUyUjAx3b3Jrc3BhY2VfaWSUSwGMC2Rlc2NyaXB0aW9ulGgkjApjcmVhdGVkX2F0lGg5QwoH5gkUCDAVC63XlGg+hpRSlIwLZXhwb3J0ZWRfYXSUTowKdXBkYXRlZF9hdJRoOUMKB+YJFAgwFQuuBZRoPoaUUpSMD19kamFuZ29fdmVyc2lvbpRoRnViSwKGlC4=	gAR9lC4=	\N	2022-09-28 11:56:29.226213+00	2022-09-28 11:56:34.697792+00	t	e5adc37ba5e646dc96486766f90fff25	cfdf480bf3fc455685e5b8b3a11977d0	1	\N
zulu-violet-mirror-equal	apps.sage_intacct.tasks.create_bill	\N	gASVsQMAAAAAAACMFWRqYW5nby5kYi5tb2RlbHMuYmFzZZSMDm1vZGVsX3VucGlja2xllJOUjARmeWxllIwMRXhwZW5zZUdyb3VwlIaUhZRSlH2UKIwGX3N0YXRllGgAjApNb2RlbFN0YXRllJOUKYGUfZQojAxmaWVsZHNfY2FjaGWUfZSMBGJpbGyUaAKMDHNhZ2VfaW50YWNjdJSMBEJpbGyUhpSFlFKUfZQojAZfc3RhdGWUaAspgZR9lCiMAmRilIwHZGVmYXVsdJRoDn2UjA1leHBlbnNlX2dyb3VwlGgHc4wGYWRkaW5nlIl1YowCaWSUSwiMEGV4cGVuc2VfZ3JvdXBfaWSUSwOMCXZlbmRvcl9pZJSMBTIwMDQzlIwLZGVzY3JpcHRpb26UfZQojAlyZXBvcnRfaWSUjAxycEJmNWlicVVUNkKUjApleHBlbnNlX2lklIwMdHhUSGZFUFdPRU9wlIwLZnVuZF9zb3VyY2WUjANDQ0OUjAxjbGFpbV9udW1iZXKUjA5DLzIwMjIvMDkvUi8yM5SMDmVtcGxveWVlX2VtYWlslIwQYXNod2luLnRAZnlsZS5pbpR1jARtZW1vlIw7Q29ycG9yYXRlIENyZWRpdCBDYXJkIGV4cGVuc2UgLSBDLzIwMjIvMDkvUi8yMyAtIDI4LzA5LzIwMjKUjAhjdXJyZW5jeZSMA1VTRJSMCXN1cGRvY19pZJROjBB0cmFuc2FjdGlvbl9kYXRllIwTMjAyMi0wOS0yOFQxMTo1NjozNpSMDnBheW1lbnRfc3luY2VklImMFHBhaWRfb25fc2FnZV9pbnRhY2N0lImMCmNyZWF0ZWRfYXSUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH5gkcCzgkA/lVlIwEcHl0epSMBF9VVEOUk5QpUpSGlFKUjAp1cGRhdGVkX2F0lGg7QwoH5gkcCzgkA/mulGhAhpRSlIwPX2RqYW5nb192ZXJzaW9ulIwGMy4xLjE0lHVic2geiWgajAdkZWZhdWx0lHVijAJpZJRLA4wLZnVuZF9zb3VyY2WUjANDQ0OUjAx3b3Jrc3BhY2VfaWSUSwGMC2Rlc2NyaXB0aW9ulGgkjApjcmVhdGVkX2F0lGg7QwoH5gkUCDgyAj9MlGhAhpRSlIwLZXhwb3J0ZWRfYXSUTowKdXBkYXRlZF9hdJRoO0MKB+YJFAg4MgI/fJRoQIaUUpSMD19kamFuZ29fdmVyc2lvbpRoSHViSwSGlC4=	gAR9lC4=	\N	2022-09-28 11:56:33.945362+00	2022-09-28 11:56:37.756708+00	t	c9cef20a69ac4e64b21cd6f460435330	8411b791379d452c90d082aa158668a4	1	\N
king-texas-timing-quiet	apps.mappings.tasks.async_auto_map_employees	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-29 12:09:11.665781+00	2022-09-29 12:09:26.068827+00	t	7820d0fa2f7f4ac78c1a5e283560a143	2	1	import
twenty-tennis-stream-cold	apps.sage_intacct.tasks.create_ap_payment	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-29 12:09:11.684809+00	2022-09-29 12:09:26.511365+00	t	334370e333c54c669f6bc9e876d3ec60	6	1	\N
muppet-delta-uniform-alanine	apps.mappings.tasks.auto_create_vendors_as_merchants	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-29 12:09:11.677356+00	2022-09-29 12:09:27.232264+00	t	3bdcf280bd6c42a197ad24f932ce39c7	4	1	\N
delta-washington-king-triple	apps.mappings.tasks.auto_create_project_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-29 12:09:11.659031+00	2022-09-29 12:09:30.836702+00	t	54ab7ab7396741eea35de26e72b73c18	5	1	\N
michigan-west-fourteen-seven	apps.mappings.tasks.auto_create_tax_codes_mappings	\N	gASVBQAAAAAAAABLAYWULg==	gAR9lC4=	\N	2022-09-29 12:09:11.671086+00	2022-09-29 12:09:34.826193+00	t	72495cee26334ea9ad64b337f757c4a6	3	1	\N
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
\.


--
-- Data for Name: employee_mappings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.employee_mappings (id, created_at, updated_at, destination_card_account_id, destination_employee_id, destination_vendor_id, source_employee_id, workspace_id) FROM stdin;
1	2022-09-20 08:40:23.121338+00	2022-09-20 08:40:23.121391+00	\N	707	699	1	1
\.


--
-- Data for Name: errors; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.errors (id, type, is_resolved, error_title, error_detail, created_at, updated_at, expense_attribute_id, expense_group_id, workspace_id, article_link, attribute_type, is_parsed, repetition_count, mapping_error_expense_group_ids) FROM stdin;
\.


--
-- Data for Name: expense_attributes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_attributes (id, attribute_type, display_name, value, source_id, created_at, updated_at, workspace_id, active, detail, auto_mapped, auto_created) FROM stdin;
2	EMPLOYEE	Employee	nilesh.p+123@fyle.in	ouEPFtpfacUg	2022-09-20 08:39:02.395739+00	2022-09-20 08:39:02.39597+00	1	\N	{"user_id": "usHDmw44Qmmy", "location": null, "full_name": "Brad Pitt", "department": null, "department_id": null, "employee_code": null, "department_code": null}	f	f
3	EMPLOYEE	Employee	user2@fyleforgotham.in	ou8TYuw4AxVG	2022-09-20 08:39:02.396218+00	2022-09-20 08:39:02.396251+00	1	\N	{"user_id": "usBlCjf2LQFc", "location": null, "full_name": "Brian Foster", "department": "Department 1", "department_id": "deptDhMjvs45aT", "employee_code": null, "department_code": null}	f	f
4	EMPLOYEE	Employee	user5@fyleforgotham.in	ouwVEj13iF6S	2022-09-20 08:39:02.396385+00	2022-09-20 08:39:02.396921+00	1	\N	{"user_id": "usJNh5yEotAI", "location": null, "full_name": "Chris Curtis", "department": "Department 1", "department_id": "deptDhMjvs45aT", "employee_code": null, "department_code": null}	f	f
5	EMPLOYEE	Employee	nilesh.p+167@fyle.in	oufShLZ4Yvn3	2022-09-20 08:39:02.397455+00	2022-09-20 08:39:02.397491+00	1	\N	{"user_id": "us8W8MDHAyCq", "location": null, "full_name": "Vikrant Messi", "department": null, "department_id": null, "employee_code": null, "department_code": null}	f	f
6	EMPLOYEE	Employee	nilesh.p@fyle.in	ouYbK261N8dp	2022-09-20 08:39:02.397943+00	2022-09-20 08:39:02.398056+00	1	\N	{"user_id": "usAQ5SpEekLK", "location": null, "full_name": "Nilesh Pant", "department": null, "department_id": null, "employee_code": null, "department_code": null}	f	f
7	EMPLOYEE	Employee	user9@fyleforgotham.in	ouh41Vnv7pl3	2022-09-20 08:39:02.403375+00	2022-09-20 08:39:02.403498+00	1	\N	{"user_id": "usjFy17trWLb", "location": null, "full_name": "Justin Glass", "department": "Department 3", "department_id": "dept0DswoMIby7", "employee_code": null, "department_code": null}	f	f
8	EMPLOYEE	Employee	user8@fyleforgotham.in	ouZF0bfmC1DV	2022-09-20 08:39:02.403952+00	2022-09-20 08:39:02.40401+00	1	\N	{"user_id": "us9jthy9XTZE", "location": null, "full_name": "Jessica Lane", "department": "Department 2", "department_id": "deptgZF9aUB0tH", "employee_code": null, "department_code": null}	f	f
9	EMPLOYEE	Employee	user7@fyleforgotham.in	ouT8HYOj1GYZ	2022-09-20 08:39:02.404323+00	2022-09-20 08:39:02.404388+00	1	\N	{"user_id": "usL3rGiHpp8q", "location": null, "full_name": "James Taylor", "department": "Department 4", "department_id": "depttugt5POp4K", "employee_code": null, "department_code": null}	f	f
10	EMPLOYEE	Employee	user6@fyleforgotham.in	ou5XWYQjmzym	2022-09-20 08:39:02.404476+00	2022-09-20 08:39:02.404591+00	1	\N	{"user_id": "usF2lrDTIZei", "location": null, "full_name": "Victor Martinez", "department": "Department 3", "department_id": "dept0DswoMIby7", "employee_code": null, "department_code": null}	f	f
11	EMPLOYEE	Employee	user4@fyleforgotham.in	ouEetwpFkf3F	2022-09-20 08:39:02.404731+00	2022-09-20 08:39:02.404772+00	1	\N	{"user_id": "usXk2TVwvJCf", "location": null, "full_name": "Samantha Washington", "department": "Department 3", "department_id": "dept0DswoMIby7", "employee_code": null, "department_code": null}	f	f
12	EMPLOYEE	Employee	user3@fyleforgotham.in	ounUmTSUyiHX	2022-09-20 08:39:02.404881+00	2022-09-20 08:39:02.404914+00	1	\N	{"user_id": "usYH6d98zJGT", "location": null, "full_name": "Natalie Pope", "department": "Department 1", "department_id": "deptDhMjvs45aT", "employee_code": null, "department_code": null}	f	f
13	EMPLOYEE	Employee	user1@fyleforgotham.in	ouVT4YfloipJ	2022-09-20 08:39:02.405826+00	2022-09-20 08:39:02.405886+00	1	\N	{"user_id": "usRKNmaNoXTy", "location": null, "full_name": "Joshua Wood", "department": "Department 2", "department_id": "deptgZF9aUB0tH", "employee_code": null, "department_code": null}	f	f
14	EMPLOYEE	Employee	user10@fyleforgotham.in	ou7yyjvEaliS	2022-09-20 08:39:02.406018+00	2022-09-20 08:39:02.406057+00	1	\N	{"user_id": "usH1U6GUQgbT", "location": null, "full_name": "Matthew Estrada", "department": "Department 4", "department_id": "depttugt5POp4K", "employee_code": null, "department_code": null}	f	f
15	EMPLOYEE	Employee	admin1@fyleforgotham.in	ouECRFhw3AjY	2022-09-20 08:39:02.406132+00	2022-09-20 08:39:02.40673+00	1	\N	{"user_id": "usnplBhNoBFN", "location": null, "full_name": "Theresa Brown", "department": null, "department_id": null, "employee_code": null, "department_code": null}	f	f
16	EMPLOYEE	Employee	owner@fyleforgotham.in	ouT4EarnaThA	2022-09-20 08:39:02.406866+00	2022-09-20 08:39:02.406922+00	1	\N	{"user_id": "uspg0D51Nts1", "location": null, "full_name": "Fyle For Arkham Asylum", "department": null, "department_id": null, "employee_code": null, "department_code": null}	f	f
17	EMPLOYEE	Employee	approver1@fyleforgotham.in	ouMvD0iJ0pXK	2022-09-20 08:39:02.407003+00	2022-09-20 08:39:02.407036+00	1	\N	{"user_id": "usAsCHVckAu8", "location": null, "full_name": "Ryan Gallagher", "department": null, "department_id": null, "employee_code": null, "department_code": null}	f	f
18912	EMPLOYEE	Employee	user48888@fyleforgotham.in	ouMvD0iJ0pX2	2022-09-20 08:39:02.407003+00	2022-09-20 08:39:02.407036+00	1	\N	{"user_id": "usAsCHVckau8", "location": null, "full_name": "Wow User", "department": null, "department_id": null, "employee_code": null, "department_code": null}	f	f
634	PROJECT	Project	goat	304630	2022-09-20 08:39:06.832998+00	2022-09-20 08:39:06.833037+00	1	t	\N	f	f
2137	COST_CENTER	Cost Center	Izio	10113	2022-09-20 08:39:10.414746+00	2022-09-20 08:39:10.414773+00	1	\N	\N	f	f
3178	MERCHANT	Merchant	Entity V500	852	2022-09-20 08:40:24.029136+00	2022-09-20 08:40:24.029271+00	1	\N	\N	f	f
1661	PROJECT	Project	TSM	247773	2022-09-20 08:39:09.282688+00	2022-09-20 08:39:09.282717+00	1	t	\N	f	f
1918	COST_CENTER	Cost Center	Quimm	10216	2022-09-20 08:39:10.306136+00	2022-09-20 08:39:10.30628+00	1	\N	\N	f	f
1874	COST_CENTER	Cost Center	Amy's Bird Sanctuary	13710	2022-09-20 08:39:10.293069+00	2022-09-20 08:39:10.293116+00	1	\N	\N	f	f
1875	COST_CENTER	Cost Center	Bill's Windsurf Shop	13711	2022-09-20 08:39:10.293189+00	2022-09-20 08:39:10.29322+00	1	\N	\N	f	f
1876	COST_CENTER	Cost Center	Cool Cars	13712	2022-09-20 08:39:10.293285+00	2022-09-20 08:39:10.293315+00	1	\N	\N	f	f
1877	COST_CENTER	Cost Center	Diego Rodriguez	13713	2022-09-20 08:39:10.293377+00	2022-09-20 08:39:10.293406+00	1	\N	\N	f	f
1878	COST_CENTER	Cost Center	Dukes Basketball Camp	13714	2022-09-20 08:39:10.293468+00	2022-09-20 08:39:10.293497+00	1	\N	\N	f	f
1879	COST_CENTER	Cost Center	Dylan Sollfrank	13715	2022-09-20 08:39:10.293761+00	2022-09-20 08:39:10.293882+00	1	\N	\N	f	f
1880	COST_CENTER	Cost Center	Freeman Sporting Goods	13716	2022-09-20 08:39:10.293966+00	2022-09-20 08:39:10.293995+00	1	\N	\N	f	f
1881	COST_CENTER	Cost Center	Freeman Sporting Goods:0969 Ocean View Road	13717	2022-09-20 08:39:10.294059+00	2022-09-20 08:39:10.294088+00	1	\N	\N	f	f
1882	COST_CENTER	Cost Center	Freeman Sporting Goods:55 Twin Lane	13718	2022-09-20 08:39:10.29415+00	2022-09-20 08:39:10.294179+00	1	\N	\N	f	f
1883	COST_CENTER	Cost Center	Geeta Kalapatapu	13719	2022-09-20 08:39:10.294242+00	2022-09-20 08:39:10.294271+00	1	\N	\N	f	f
1884	COST_CENTER	Cost Center	Gevelber Photography	13720	2022-09-20 08:39:10.294423+00	2022-09-20 08:39:10.294535+00	1	\N	\N	f	f
1885	COST_CENTER	Cost Center	goat	13721	2022-09-20 08:39:10.294619+00	2022-09-20 08:39:10.29466+00	1	\N	\N	f	f
1886	COST_CENTER	Cost Center	Jeff's Jalopies	13722	2022-09-20 08:39:10.294722+00	2022-09-20 08:39:10.294751+00	1	\N	\N	f	f
1887	COST_CENTER	Cost Center	John Melton	13723	2022-09-20 08:39:10.294811+00	2022-09-20 08:39:10.294841+00	1	\N	\N	f	f
1888	COST_CENTER	Cost Center	Kate Whelan	13724	2022-09-20 08:39:10.294901+00	2022-09-20 08:39:10.29493+00	1	\N	\N	f	f
1889	COST_CENTER	Cost Center	Kookies by Kathy	13725	2022-09-20 08:39:10.294992+00	2022-09-20 08:39:10.295021+00	1	\N	\N	f	f
1890	COST_CENTER	Cost Center	Mark Cho	13726	2022-09-20 08:39:10.29508+00	2022-09-20 08:39:10.295109+00	1	\N	\N	f	f
1891	COST_CENTER	Cost Center	Paulsen Medical Supplies	13727	2022-09-20 08:39:10.295169+00	2022-09-20 08:39:10.295198+00	1	\N	\N	f	f
1892	COST_CENTER	Cost Center	Rago Travel Agency	13728	2022-09-20 08:39:10.295258+00	2022-09-20 08:39:10.295287+00	1	\N	\N	f	f
1893	COST_CENTER	Cost Center	Red Rock Diner	13729	2022-09-20 08:39:10.295455+00	2022-09-20 08:39:10.29554+00	1	\N	\N	f	f
1894	COST_CENTER	Cost Center	Rondonuwu Fruit and Vegi	13730	2022-09-20 08:39:10.295595+00	2022-09-20 08:39:10.295624+00	1	\N	\N	f	f
1895	COST_CENTER	Cost Center	Shara Barnett	13731	2022-09-20 08:39:10.295685+00	2022-09-20 08:39:10.295714+00	1	\N	\N	f	f
1896	COST_CENTER	Cost Center	Shara Barnett:Barnett Design	13732	2022-09-20 08:39:10.295774+00	2022-09-20 08:39:10.295803+00	1	\N	\N	f	f
681	PROJECT	Project	Project 5	203313	2022-09-20 08:39:06.849026+00	2022-09-20 08:39:06.849055+00	1	t	\N	f	f
1897	COST_CENTER	Cost Center	Sonnenschein Family Store	13733	2022-09-20 08:39:10.296923+00	2022-09-20 08:39:10.297618+00	1	\N	\N	f	f
1898	COST_CENTER	Cost Center	Sushi by Katsuyuki	13734	2022-09-20 08:39:10.298005+00	2022-09-20 08:39:10.298037+00	1	\N	\N	f	f
1899	COST_CENTER	Cost Center	Travis Waldron	13735	2022-09-20 08:39:10.298423+00	2022-09-20 08:39:10.298455+00	1	\N	\N	f	f
1900	COST_CENTER	Cost Center	Video Games by Dan	13736	2022-09-20 08:39:10.298671+00	2022-09-20 08:39:10.298849+00	1	\N	\N	f	f
1901	COST_CENTER	Cost Center	Weiskopf Consulting	13737	2022-09-20 08:39:10.299067+00	2022-09-20 08:39:10.299099+00	1	\N	\N	f	f
1902	COST_CENTER	Cost Center	FAE:Mini FAE	12489	2022-09-20 08:39:10.299396+00	2022-09-20 08:39:10.299575+00	1	\N	\N	f	f
1903	COST_CENTER	Cost Center	Portore	10201	2022-09-20 08:39:10.299794+00	2022-09-20 08:39:10.299825+00	1	\N	\N	f	f
1904	COST_CENTER	Cost Center	Powell Clean Tech	10202	2022-09-20 08:39:10.300037+00	2022-09-20 08:39:10.300182+00	1	\N	\N	f	f
1905	COST_CENTER	Cost Center	PPC Ltd.	10203	2022-09-20 08:39:10.300445+00	2022-09-20 08:39:10.300627+00	1	\N	\N	f	f
1906	COST_CENTER	Cost Center	Premier FMCG	10204	2022-09-20 08:39:10.300846+00	2022-09-20 08:39:10.300878+00	1	\N	\N	f	f
1907	COST_CENTER	Cost Center	Premier Inc	10205	2022-09-20 08:39:10.301403+00	2022-09-20 08:39:10.301642+00	1	\N	\N	f	f
1908	COST_CENTER	Cost Center	Prescott Pharmaceuticals	10206	2022-09-20 08:39:10.30188+00	2022-09-20 08:39:10.301913+00	1	\N	\N	f	f
1909	COST_CENTER	Cost Center	Primatech Paper	10207	2022-09-20 08:39:10.302186+00	2022-09-20 08:39:10.302215+00	1	\N	\N	f	f
1910	COST_CENTER	Cost Center	Primedia	10208	2022-09-20 08:39:10.302501+00	2022-09-20 08:39:10.302736+00	1	\N	\N	f	f
1911	COST_CENTER	Cost Center	Primedia Broadcasting	10209	2022-09-20 08:39:10.303095+00	2022-09-20 08:39:10.303544+00	1	\N	\N	f	f
1912	COST_CENTER	Cost Center	Projo	10210	2022-09-20 08:39:10.303819+00	2022-09-20 08:39:10.304049+00	1	\N	\N	f	f
1913	COST_CENTER	Cost Center	Proton Centric	10211	2022-09-20 08:39:10.304433+00	2022-09-20 08:39:10.304664+00	1	\N	\N	f	f
1914	COST_CENTER	Cost Center	Proweb	10212	2022-09-20 08:39:10.304892+00	2022-09-20 08:39:10.305076+00	1	\N	\N	f	f
1915	COST_CENTER	Cost Center	PUTCO	10213	2022-09-20 08:39:10.305319+00	2022-09-20 08:39:10.30535+00	1	\N	\N	f	f
1916	COST_CENTER	Cost Center	Quallaby Corporation	10214	2022-09-20 08:39:10.305517+00	2022-09-20 08:39:10.305718+00	1	\N	\N	f	f
1917	COST_CENTER	Cost Center	Quantum Networks	10215	2022-09-20 08:39:10.305912+00	2022-09-20 08:39:10.305942+00	1	\N	\N	f	f
1919	COST_CENTER	Cost Center	Rand Corporation	10217	2022-09-20 08:39:10.30641+00	2022-09-20 08:39:10.306569+00	1	\N	\N	f	f
1920	COST_CENTER	Cost Center	RCL Foods	10218	2022-09-20 08:39:10.306889+00	2022-09-20 08:39:10.30692+00	1	\N	\N	f	f
1921	COST_CENTER	Cost Center	RedFin Insurance	10219	2022-09-20 08:39:10.307118+00	2022-09-20 08:39:10.307239+00	1	\N	\N	f	f
1922	COST_CENTER	Cost Center	Render	10220	2022-09-20 08:39:10.307369+00	2022-09-20 08:39:10.307529+00	1	\N	\N	f	f
1923	COST_CENTER	Cost Center	Renegade Furniture Group	10221	2022-09-20 08:39:10.307718+00	2022-09-20 08:39:10.307748+00	1	\N	\N	f	f
1924	COST_CENTER	Cost Center	Rhycero	10222	2022-09-20 08:39:10.339568+00	2022-09-20 08:39:10.339612+00	1	\N	\N	f	f
1925	COST_CENTER	Cost Center	Riffwire	10223	2022-09-20 08:39:10.339688+00	2022-09-20 08:39:10.339719+00	1	\N	\N	f	f
1926	COST_CENTER	Cost Center	Riovic	10224	2022-09-20 08:39:10.339786+00	2022-09-20 08:39:10.339816+00	1	\N	\N	f	f
1927	COST_CENTER	Cost Center	Rossum Corporation	10225	2022-09-20 08:39:10.339881+00	2022-09-20 08:39:10.339911+00	1	\N	\N	f	f
1928	COST_CENTER	Cost Center	Rovos Rail	10226	2022-09-20 08:39:10.339974+00	2022-09-20 08:39:10.340004+00	1	\N	\N	f	f
1929	COST_CENTER	Cost Center	Roxxon	10227	2022-09-20 08:39:10.340066+00	2022-09-20 08:39:10.340096+00	1	\N	\N	f	f
1930	COST_CENTER	Cost Center	Sagacent Finance	10228	2022-09-20 08:39:10.340158+00	2022-09-20 08:39:10.340187+00	1	\N	\N	f	f
1931	COST_CENTER	Cost Center	Sailthru	10229	2022-09-20 08:39:10.340249+00	2022-09-20 08:39:10.340278+00	1	\N	\N	f	f
1932	COST_CENTER	Cost Center	Sanlam	10230	2022-09-20 08:39:10.340339+00	2022-09-20 08:39:10.340369+00	1	\N	\N	f	f
1933	COST_CENTER	Cost Center	Sasol	10231	2022-09-20 08:39:10.340633+00	2022-09-20 08:39:10.340667+00	1	\N	\N	f	f
1934	COST_CENTER	Cost Center	Seburo	10232	2022-09-20 08:39:10.340731+00	2022-09-20 08:39:10.34076+00	1	\N	\N	f	f
1935	COST_CENTER	Cost Center	Sempra Energy	10233	2022-09-20 08:39:10.340821+00	2022-09-20 08:39:10.34085+00	1	\N	\N	f	f
1936	COST_CENTER	Cost Center	Serrano Genomics	10234	2022-09-20 08:39:10.34091+00	2022-09-20 08:39:10.340938+00	1	\N	\N	f	f
1937	COST_CENTER	Cost Center	Shinra Electric	10235	2022-09-20 08:39:10.340998+00	2022-09-20 08:39:10.341027+00	1	\N	\N	f	f
1938	COST_CENTER	Cost Center	Shoprite	10236	2022-09-20 08:39:10.341087+00	2022-09-20 08:39:10.341115+00	1	\N	\N	f	f
3179	MERCHANT	Merchant	Entity V600	852	2022-09-20 08:40:24.029339+00	2022-09-20 08:40:24.029366+00	1	\N	\N	f	f
1939	COST_CENTER	Cost Center	Simeon	10237	2022-09-20 08:39:10.341175+00	2022-09-20 08:39:10.341204+00	1	\N	\N	f	f
1940	COST_CENTER	Cost Center	Skimia	10238	2022-09-20 08:39:10.341263+00	2022-09-20 08:39:10.341292+00	1	\N	\N	f	f
1941	COST_CENTER	Cost Center	Skinte	10239	2022-09-20 08:39:10.341518+00	2022-09-20 08:39:10.341582+00	1	\N	\N	f	f
1942	COST_CENTER	Cost Center	Skivee	10240	2022-09-20 08:39:10.341679+00	2022-09-20 08:39:10.341709+00	1	\N	\N	f	f
1943	COST_CENTER	Cost Center	Sonicwall, Inc.	10241	2022-09-20 08:39:10.341772+00	2022-09-20 08:39:10.341801+00	1	\N	\N	f	f
1944	COST_CENTER	Cost Center	South African Breweries	10242	2022-09-20 08:39:10.341863+00	2022-09-20 08:39:10.341892+00	1	\N	\N	f	f
1945	COST_CENTER	Cost Center	South African Broadcasting Corporation	10243	2022-09-20 08:39:10.341954+00	2022-09-20 08:39:10.341983+00	1	\N	\N	f	f
1946	COST_CENTER	Cost Center	South Bay Medical Center	10244	2022-09-20 08:39:10.342043+00	2022-09-20 08:39:10.342073+00	1	\N	\N	f	f
1947	COST_CENTER	Cost Center	Southern Orthopedics	10245	2022-09-20 08:39:10.342133+00	2022-09-20 08:39:10.342162+00	1	\N	\N	f	f
1948	COST_CENTER	Cost Center	Soylent Corporation	10246	2022-09-20 08:39:10.342222+00	2022-09-20 08:39:10.342251+00	1	\N	\N	f	f
1949	COST_CENTER	Cost Center	Spencer, Scott and Dwyer	10247	2022-09-20 08:39:10.342317+00	2022-09-20 08:39:10.342346+00	1	\N	\N	f	f
1950	COST_CENTER	Cost Center	Spine Rehab Center	10248	2022-09-20 08:39:10.342757+00	2022-09-20 08:39:10.342821+00	1	\N	\N	f	f
1951	COST_CENTER	Cost Center	Standard Bank	10249	2022-09-20 08:39:10.342962+00	2022-09-20 08:39:10.343008+00	1	\N	\N	f	f
1952	COST_CENTER	Cost Center	Stark Industries	10250	2022-09-20 08:39:10.343136+00	2022-09-20 08:39:10.343402+00	1	\N	\N	f	f
1953	COST_CENTER	Cost Center	StarSat, South Africa	10251	2022-09-20 08:39:10.34353+00	2022-09-20 08:39:10.343577+00	1	\N	\N	f	f
1954	COST_CENTER	Cost Center	Stay Puft	10252	2022-09-20 08:39:10.343697+00	2022-09-20 08:39:10.343745+00	1	\N	\N	f	f
1955	COST_CENTER	Cost Center	Stoxnetwork Corporation	10253	2022-09-20 08:39:10.343868+00	2022-09-20 08:39:10.344484+00	1	\N	\N	f	f
1956	COST_CENTER	Cost Center	Strickland Propane	10254	2022-09-20 08:39:10.344669+00	2022-09-20 08:39:10.344725+00	1	\N	\N	f	f
1957	COST_CENTER	Cost Center	Sunshine Desserts	10255	2022-09-20 08:39:10.344862+00	2022-09-20 08:39:10.344925+00	1	\N	\N	f	f
1958	COST_CENTER	Cost Center	Talcomp Management Services	10256	2022-09-20 08:39:10.345428+00	2022-09-20 08:39:10.345561+00	1	\N	\N	f	f
1959	COST_CENTER	Cost Center	Tanoodle	10257	2022-09-20 08:39:10.345678+00	2022-09-20 08:39:10.345724+00	1	\N	\N	f	f
1960	COST_CENTER	Cost Center	Telkom	10258	2022-09-20 08:39:10.345841+00	2022-09-20 08:39:10.345886+00	1	\N	\N	f	f
1961	COST_CENTER	Cost Center	Telkom Mobile	10259	2022-09-20 08:39:10.34602+00	2022-09-20 08:39:10.346075+00	1	\N	\N	f	f
1962	COST_CENTER	Cost Center	TetraCorp	10260	2022-09-20 08:39:10.346185+00	2022-09-20 08:39:10.346225+00	1	\N	\N	f	f
1963	COST_CENTER	Cost Center	The android's Dungeon	10261	2022-09-20 08:39:10.346324+00	2022-09-20 08:39:10.346364+00	1	\N	\N	f	f
1964	COST_CENTER	Cost Center	The HCI Group	10262	2022-09-20 08:39:10.346608+00	2022-09-20 08:39:10.346657+00	1	\N	\N	f	f
1965	COST_CENTER	Cost Center	The Vanguard Group, Inc.	10263	2022-09-20 08:39:10.346916+00	2022-09-20 08:39:10.346971+00	1	\N	\N	f	f
1966	COST_CENTER	Cost Center	ThinkLite	10264	2022-09-20 08:39:10.347111+00	2022-09-20 08:39:10.347143+00	1	\N	\N	f	f
1967	COST_CENTER	Cost Center	Thoughtstorm	10265	2022-09-20 08:39:10.347211+00	2022-09-20 08:39:10.34724+00	1	\N	\N	f	f
1968	COST_CENTER	Cost Center	Thoughtworks	10266	2022-09-20 08:39:10.347303+00	2022-09-20 08:39:10.347333+00	1	\N	\N	f	f
1969	COST_CENTER	Cost Center	Tiger Brands	10267	2022-09-20 08:39:10.347508+00	2022-09-20 08:39:10.347538+00	1	\N	\N	f	f
1970	COST_CENTER	Cost Center	Times Media Group	10268	2022-09-20 08:39:10.347601+00	2022-09-20 08:39:10.34763+00	1	\N	\N	f	f
1971	COST_CENTER	Cost Center	Titanium Corporation Inc.	10269	2022-09-20 08:39:10.347705+00	2022-09-20 08:39:10.347728+00	1	\N	\N	f	f
1972	COST_CENTER	Cost Center	Tongaat Hulett	10270	2022-09-20 08:39:10.347789+00	2022-09-20 08:39:10.347819+00	1	\N	\N	f	f
1973	COST_CENTER	Cost Center	Topdrive	10271	2022-09-20 08:39:10.34788+00	2022-09-20 08:39:10.347909+00	1	\N	\N	f	f
1974	COST_CENTER	Cost Center	Topicstorm	10272	2022-09-20 08:39:10.37308+00	2022-09-20 08:39:10.373404+00	1	\N	\N	f	f
1975	COST_CENTER	Cost Center	Topicware	10273	2022-09-20 08:39:10.373832+00	2022-09-20 08:39:10.373864+00	1	\N	\N	f	f
1976	COST_CENTER	Cost Center	Topiczoom	10274	2022-09-20 08:39:10.374098+00	2022-09-20 08:39:10.374371+00	1	\N	\N	f	f
1977	COST_CENTER	Cost Center	Trade Federation	10275	2022-09-20 08:39:10.374617+00	2022-09-20 08:39:10.374648+00	1	\N	\N	f	f
1978	COST_CENTER	Cost Center	Transnet	10276	2022-09-20 08:39:10.374882+00	2022-09-20 08:39:10.375104+00	1	\N	\N	f	f
1979	COST_CENTER	Cost Center	Treadstone	10277	2022-09-20 08:39:10.375392+00	2022-09-20 08:39:10.375527+00	1	\N	\N	f	f
1980	COST_CENTER	Cost Center	Tricell	10278	2022-09-20 08:39:10.375747+00	2022-09-20 08:39:10.37578+00	1	\N	\N	f	f
1981	COST_CENTER	Cost Center	Trilith	10279	2022-09-20 08:39:10.375976+00	2022-09-20 08:39:10.376131+00	1	\N	\N	f	f
1982	COST_CENTER	Cost Center	TriOptimum	10280	2022-09-20 08:39:10.376376+00	2022-09-20 08:39:10.376405+00	1	\N	\N	f	f
1983	COST_CENTER	Cost Center	Trudeo	10281	2022-09-20 08:39:10.376584+00	2022-09-20 08:39:10.376732+00	1	\N	\N	f	f
1984	COST_CENTER	Cost Center	Trunyx	10282	2022-09-20 08:39:10.376932+00	2022-09-20 08:39:10.376959+00	1	\N	\N	f	f
1985	COST_CENTER	Cost Center	Twitterbeat	10283	2022-09-20 08:39:10.377464+00	2022-09-20 08:39:10.377624+00	1	\N	\N	f	f
1986	COST_CENTER	Cost Center	Tyrell Corp.	10284	2022-09-20 08:39:10.377823+00	2022-09-20 08:39:10.377854+00	1	\N	\N	f	f
1987	COST_CENTER	Cost Center	Ultor	10285	2022-09-20 08:39:10.378049+00	2022-09-20 08:39:10.378177+00	1	\N	\N	f	f
1988	COST_CENTER	Cost Center	Umbrella Corporation	10286	2022-09-20 08:39:10.378398+00	2022-09-20 08:39:10.378553+00	1	\N	\N	f	f
1989	COST_CENTER	Cost Center	Union Aerospace Corporation	10287	2022-09-20 08:39:10.378747+00	2022-09-20 08:39:10.378777+00	1	\N	\N	f	f
1990	COST_CENTER	Cost Center	United Liberty Paper	10288	2022-09-20 08:39:10.378965+00	2022-09-20 08:39:10.379122+00	1	\N	\N	f	f
1991	COST_CENTER	Cost Center	United Methodist Communications	10289	2022-09-20 08:39:10.379387+00	2022-09-20 08:39:10.379417+00	1	\N	\N	f	f
1992	COST_CENTER	Cost Center	United Robotronics	10290	2022-09-20 08:39:10.379582+00	2022-09-20 08:39:10.379612+00	1	\N	\N	f	f
1993	COST_CENTER	Cost Center	United Security Bank	10291	2022-09-20 08:39:10.379672+00	2022-09-20 08:39:10.379701+00	1	\N	\N	f	f
1994	COST_CENTER	Cost Center	Universal Exports	10292	2022-09-20 08:39:10.379762+00	2022-09-20 08:39:10.379791+00	1	\N	\N	f	f
1995	COST_CENTER	Cost Center	Universal Terraforming	10293	2022-09-20 08:39:10.379852+00	2022-09-20 08:39:10.379881+00	1	\N	\N	f	f
1996	COST_CENTER	Cost Center	U-North	10294	2022-09-20 08:39:10.379942+00	2022-09-20 08:39:10.37997+00	1	\N	\N	f	f
1997	COST_CENTER	Cost Center	Uplift Services	10295	2022-09-20 08:39:10.380031+00	2022-09-20 08:39:10.38006+00	1	\N	\N	f	f
1998	COST_CENTER	Cost Center	Uplink	10296	2022-09-20 08:39:10.38012+00	2022-09-20 08:39:10.380148+00	1	\N	\N	f	f
1999	COST_CENTER	Cost Center	Upton-Webber	10297	2022-09-20 08:39:10.380208+00	2022-09-20 08:39:10.380237+00	1	\N	\N	f	f
2000	COST_CENTER	Cost Center	Vaillante	10298	2022-09-20 08:39:10.380298+00	2022-09-20 08:39:10.380327+00	1	\N	\N	f	f
2001	COST_CENTER	Cost Center	Vandelay Industries	10299	2022-09-20 08:39:10.380473+00	2022-09-20 08:39:10.380502+00	1	\N	\N	f	f
2002	COST_CENTER	Cost Center	Vapid Battery	10300	2022-09-20 08:39:10.380562+00	2022-09-20 08:39:10.380592+00	1	\N	\N	f	f
2003	COST_CENTER	Cost Center	Veridian Dynamics	10301	2022-09-20 08:39:10.380652+00	2022-09-20 08:39:10.380681+00	1	\N	\N	f	f
2004	COST_CENTER	Cost Center	VersaLife Corporation	10302	2022-09-20 08:39:10.380741+00	2022-09-20 08:39:10.38077+00	1	\N	\N	f	f
2005	COST_CENTER	Cost Center	Vertous	10303	2022-09-20 08:39:10.380829+00	2022-09-20 08:39:10.380858+00	1	\N	\N	f	f
2006	COST_CENTER	Cost Center	Virtela Communications	10304	2022-09-20 08:39:10.380918+00	2022-09-20 08:39:10.380947+00	1	\N	\N	f	f
2007	COST_CENTER	Cost Center	Voolith	10305	2022-09-20 08:39:10.381007+00	2022-09-20 08:39:10.381036+00	1	\N	\N	f	f
2008	COST_CENTER	Cost Center	Voomm	10306	2022-09-20 08:39:10.381095+00	2022-09-20 08:39:10.381124+00	1	\N	\N	f	f
2009	COST_CENTER	Cost Center	Voonix	10307	2022-09-20 08:39:10.381184+00	2022-09-20 08:39:10.381213+00	1	\N	\N	f	f
2010	COST_CENTER	Cost Center	Wauwatosa Medical Group	10308	2022-09-20 08:39:10.381274+00	2022-09-20 08:39:10.381303+00	1	\N	\N	f	f
2011	COST_CENTER	Cost Center	Wayne Enterprises	10309	2022-09-20 08:39:10.381488+00	2022-09-20 08:39:10.381512+00	1	\N	\N	f	f
2012	COST_CENTER	Cost Center	Wernham Hogg	10310	2022-09-20 08:39:10.381583+00	2022-09-20 08:39:10.381733+00	1	\N	\N	f	f
2013	COST_CENTER	Cost Center	West Oak Capital Group Inc	10311	2022-09-20 08:39:10.38191+00	2022-09-20 08:39:10.381939+00	1	\N	\N	f	f
2014	COST_CENTER	Cost Center	Weyland-Yutani	10312	2022-09-20 08:39:10.382+00	2022-09-20 08:39:10.382029+00	1	\N	\N	f	f
2015	COST_CENTER	Cost Center	Wikibox	10313	2022-09-20 08:39:10.382089+00	2022-09-20 08:39:10.382117+00	1	\N	\N	f	f
2016	COST_CENTER	Cost Center	Woodlands Medical Group	10314	2022-09-20 08:39:10.382177+00	2022-09-20 08:39:10.382207+00	1	\N	\N	f	f
2017	COST_CENTER	Cost Center	X-Com	10315	2022-09-20 08:39:10.382361+00	2022-09-20 08:39:10.38239+00	1	\N	\N	f	f
2018	COST_CENTER	Cost Center	Yata	10316	2022-09-20 08:39:10.38245+00	2022-09-20 08:39:10.382479+00	1	\N	\N	f	f
2019	COST_CENTER	Cost Center	YellowHammer	10317	2022-09-20 08:39:10.382539+00	2022-09-20 08:39:10.382568+00	1	\N	\N	f	f
2020	COST_CENTER	Cost Center	Yodel	10318	2022-09-20 08:39:10.382628+00	2022-09-20 08:39:10.382656+00	1	\N	\N	f	f
2021	COST_CENTER	Cost Center	Yombu	10319	2022-09-20 08:39:10.382717+00	2022-09-20 08:39:10.382746+00	1	\N	\N	f	f
2022	COST_CENTER	Cost Center	Youbridge	10320	2022-09-20 08:39:10.382806+00	2022-09-20 08:39:10.382835+00	1	\N	\N	f	f
2023	COST_CENTER	Cost Center	Yoyodyne Propulsion	10321	2022-09-20 08:39:10.382895+00	2022-09-20 08:39:10.382923+00	1	\N	\N	f	f
2024	COST_CENTER	Cost Center	Zimms	10322	2022-09-20 08:39:10.389786+00	2022-09-20 08:39:10.389827+00	1	\N	\N	f	f
2025	COST_CENTER	Cost Center	Ziodex Industries	10323	2022-09-20 08:39:10.389894+00	2022-09-20 08:39:10.389922+00	1	\N	\N	f	f
2026	COST_CENTER	Cost Center	Zoombeat	10324	2022-09-20 08:39:10.389982+00	2022-09-20 08:39:10.390158+00	1	\N	\N	f	f
2027	COST_CENTER	Cost Center	Zoozzy	10325	2022-09-20 08:39:10.390412+00	2022-09-20 08:39:10.390559+00	1	\N	\N	f	f
2028	COST_CENTER	Cost Center	De Beers	10004	2022-09-20 08:39:10.390772+00	2022-09-20 08:39:10.390799+00	1	\N	\N	f	f
2029	COST_CENTER	Cost Center	De Bortoli Wines	10005	2022-09-20 08:39:10.391413+00	2022-09-20 08:39:10.391449+00	1	\N	\N	f	f
2030	COST_CENTER	Cost Center	Defy Appliances	10006	2022-09-20 08:39:10.391524+00	2022-09-20 08:39:10.391551+00	1	\N	\N	f	f
2031	COST_CENTER	Cost Center	De Haan's Bus and Coach	10007	2022-09-20 08:39:10.391609+00	2022-09-20 08:39:10.391636+00	1	\N	\N	f	f
2032	COST_CENTER	Cost Center	Delos	10008	2022-09-20 08:39:10.391693+00	2022-09-20 08:39:10.39172+00	1	\N	\N	f	f
2033	COST_CENTER	Cost Center	Delta Electricity	10009	2022-09-20 08:39:10.391777+00	2022-09-20 08:39:10.391804+00	1	\N	\N	f	f
2034	COST_CENTER	Cost Center	Delta Hotels	10010	2022-09-20 08:39:10.39186+00	2022-09-20 08:39:10.391887+00	1	\N	\N	f	f
2035	COST_CENTER	Cost Center	Denticare Of Oklahoma	10011	2022-09-20 08:39:10.391943+00	2022-09-20 08:39:10.39197+00	1	\N	\N	f	f
2036	COST_CENTER	Cost Center	Deon International	10012	2022-09-20 08:39:10.392026+00	2022-09-20 08:39:10.392054+00	1	\N	\N	f	f
2037	COST_CENTER	Cost Center	Devbug	10013	2022-09-20 08:39:10.392109+00	2022-09-20 08:39:10.392137+00	1	\N	\N	f	f
2038	COST_CENTER	Cost Center	Devlin MacGregor	10014	2022-09-20 08:39:10.392193+00	2022-09-20 08:39:10.39222+00	1	\N	\N	f	f
2039	COST_CENTER	Cost Center	Dhaliwal Labs	10015	2022-09-20 08:39:10.392276+00	2022-09-20 08:39:10.392303+00	1	\N	\N	f	f
2040	COST_CENTER	Cost Center	Dharma Initiative	10016	2022-09-20 08:39:10.392359+00	2022-09-20 08:39:10.392503+00	1	\N	\N	f	f
682	PROJECT	Project	Project 6	203314	2022-09-20 08:39:06.84919+00	2022-09-20 08:39:06.849364+00	1	t	\N	f	f
2041	COST_CENTER	Cost Center	Dick Smith Electronics	10017	2022-09-20 08:39:10.392592+00	2022-09-20 08:39:10.39262+00	1	\N	\N	f	f
2042	COST_CENTER	Cost Center	Digital Bio	10018	2022-09-20 08:39:10.392676+00	2022-09-20 08:39:10.392704+00	1	\N	\N	f	f
2043	COST_CENTER	Cost Center	Digital Extremes	10019	2022-09-20 08:39:10.39276+00	2022-09-20 08:39:10.392787+00	1	\N	\N	f	f
2044	COST_CENTER	Cost Center	Digivation Industries	10020	2022-09-20 08:39:10.392843+00	2022-09-20 08:39:10.392871+00	1	\N	\N	f	f
2045	COST_CENTER	Cost Center	Dimension Data	10021	2022-09-20 08:39:10.392927+00	2022-09-20 08:39:10.392954+00	1	\N	\N	f	f
2046	COST_CENTER	Cost Center	Discovery Air Defence	10022	2022-09-20 08:39:10.39301+00	2022-09-20 08:39:10.393037+00	1	\N	\N	f	f
104	CATEGORY	Category	hello	184630	2022-09-20 08:39:03.373599+00	2022-09-20 08:39:03.373619+00	1	t	\N	f	f
2047	COST_CENTER	Cost Center	Divavu	10023	2022-09-20 08:39:10.393093+00	2022-09-20 08:39:10.393133+00	1	\N	\N	f	f
2048	COST_CENTER	Cost Center	Dominion Voting Systems	10024	2022-09-20 08:39:10.393838+00	2022-09-20 08:39:10.393882+00	1	\N	\N	f	f
2049	COST_CENTER	Cost Center	Donner Metals	10025	2022-09-20 08:39:10.394087+00	2022-09-20 08:39:10.394118+00	1	\N	\N	f	f
2050	COST_CENTER	Cost Center	Dorf Clark Industries	10026	2022-09-20 08:39:10.394183+00	2022-09-20 08:39:10.39421+00	1	\N	\N	f	f
2051	COST_CENTER	Cost Center	Downer Group	10027	2022-09-20 08:39:10.394485+00	2022-09-20 08:39:10.394543+00	1	\N	\N	f	f
2052	COST_CENTER	Cost Center	Duff	10028	2022-09-20 08:39:10.394608+00	2022-09-20 08:39:10.394635+00	1	\N	\N	f	f
2053	COST_CENTER	Cost Center	Dunder Mifflin	10029	2022-09-20 08:39:10.394694+00	2022-09-20 08:39:10.394721+00	1	\N	\N	f	f
2054	COST_CENTER	Cost Center	Dymocks Booksellers	10030	2022-09-20 08:39:10.394779+00	2022-09-20 08:39:10.394806+00	1	\N	\N	f	f
2055	COST_CENTER	Cost Center	Dynabox	10031	2022-09-20 08:39:10.394863+00	2022-09-20 08:39:10.39489+00	1	\N	\N	f	f
2056	COST_CENTER	Cost Center	Dynamsoft	10032	2022-09-20 08:39:10.394947+00	2022-09-20 08:39:10.394975+00	1	\N	\N	f	f
2057	COST_CENTER	Cost Center	Dynatechnics	10033	2022-09-20 08:39:10.395031+00	2022-09-20 08:39:10.395059+00	1	\N	\N	f	f
2058	COST_CENTER	Cost Center	EA Black Box	10034	2022-09-20 08:39:10.395115+00	2022-09-20 08:39:10.395142+00	1	\N	\N	f	f
2059	COST_CENTER	Cost Center	Eadel	10035	2022-09-20 08:39:10.3952+00	2022-09-20 08:39:10.395227+00	1	\N	\N	f	f
2060	COST_CENTER	Cost Center	Eagle Boys	10036	2022-09-20 08:39:10.395285+00	2022-09-20 08:39:10.395312+00	1	\N	\N	f	f
2061	COST_CENTER	Cost Center	Ecumena	10037	2022-09-20 08:39:10.395369+00	2022-09-20 08:39:10.395528+00	1	\N	\N	f	f
2062	COST_CENTER	Cost Center	Edgars	10038	2022-09-20 08:39:10.395598+00	2022-09-20 08:39:10.395626+00	1	\N	\N	f	f
2063	COST_CENTER	Cost Center	Edgeblab	10039	2022-09-20 08:39:10.395682+00	2022-09-20 08:39:10.395709+00	1	\N	\N	f	f
2064	COST_CENTER	Cost Center	Elders Limited	10040	2022-09-20 08:39:10.395765+00	2022-09-20 08:39:10.395792+00	1	\N	\N	f	f
2065	COST_CENTER	Cost Center	Electrohome	10041	2022-09-20 08:39:10.395848+00	2022-09-20 08:39:10.395875+00	1	\N	\N	f	f
2066	COST_CENTER	Cost Center	Elfin Cars	10042	2022-09-20 08:39:10.395931+00	2022-09-20 08:39:10.395958+00	1	\N	\N	f	f
2067	COST_CENTER	Cost Center	Emera	10043	2022-09-20 08:39:10.396014+00	2022-09-20 08:39:10.396041+00	1	\N	\N	f	f
2068	COST_CENTER	Cost Center	ENCOM	10044	2022-09-20 08:39:10.396097+00	2022-09-20 08:39:10.396124+00	1	\N	\N	f	f
2069	COST_CENTER	Cost Center	Entity 100	10045	2022-09-20 08:39:10.39618+00	2022-09-20 08:39:10.396207+00	1	\N	\N	f	f
2070	COST_CENTER	Cost Center	Entity 200	10046	2022-09-20 08:39:10.396262+00	2022-09-20 08:39:10.396289+00	1	\N	\N	f	f
2071	COST_CENTER	Cost Center	Entity 300	10047	2022-09-20 08:39:10.396358+00	2022-09-20 08:39:10.396494+00	1	\N	\N	f	f
2072	COST_CENTER	Cost Center	Entity 400	10048	2022-09-20 08:39:10.396562+00	2022-09-20 08:39:10.396589+00	1	\N	\N	f	f
2073	COST_CENTER	Cost Center	Entity 500	10049	2022-09-20 08:39:10.396646+00	2022-09-20 08:39:10.396673+00	1	\N	\N	f	f
2074	COST_CENTER	Cost Center	Entity 600	10050	2022-09-20 08:39:10.402003+00	2022-09-20 08:39:10.402046+00	1	\N	\N	f	f
2075	COST_CENTER	Cost Center	Entity 700	10051	2022-09-20 08:39:10.402114+00	2022-09-20 08:39:10.402143+00	1	\N	\N	f	f
2076	COST_CENTER	Cost Center	Enwave	10052	2022-09-20 08:39:10.402203+00	2022-09-20 08:39:10.40223+00	1	\N	\N	f	f
2077	COST_CENTER	Cost Center	Eskom	10053	2022-09-20 08:39:10.402289+00	2022-09-20 08:39:10.402317+00	1	\N	\N	f	f
2078	COST_CENTER	Cost Center	e.tv	10054	2022-09-20 08:39:10.402529+00	2022-09-20 08:39:10.402573+00	1	\N	\N	f	f
2079	COST_CENTER	Cost Center	Ewing Oil	10055	2022-09-20 08:39:10.402636+00	2022-09-20 08:39:10.402664+00	1	\N	\N	f	f
2080	COST_CENTER	Cost Center	Exxaro	10056	2022-09-20 08:39:10.402722+00	2022-09-20 08:39:10.402749+00	1	\N	\N	f	f
2081	COST_CENTER	Cost Center	EZ Services	10057	2022-09-20 08:39:10.402806+00	2022-09-20 08:39:10.402834+00	1	\N	\N	f	f
2082	COST_CENTER	Cost Center	Fab Seven	10058	2022-09-20 08:39:10.402891+00	2022-09-20 08:39:10.402918+00	1	\N	\N	f	f
2083	COST_CENTER	Cost Center	Fairmont Hotels and Resorts	10059	2022-09-20 08:39:10.402975+00	2022-09-20 08:39:10.403002+00	1	\N	\N	f	f
2084	COST_CENTER	Cost Center	FandP Manufacturing Inc.	10060	2022-09-20 08:39:10.403059+00	2022-09-20 08:39:10.403086+00	1	\N	\N	f	f
2085	COST_CENTER	Cost Center	Farmers of North America	10061	2022-09-20 08:39:10.403143+00	2022-09-20 08:39:10.40317+00	1	\N	\N	f	f
2086	COST_CENTER	Cost Center	Feednation	10062	2022-09-20 08:39:10.403227+00	2022-09-20 08:39:10.403255+00	1	\N	\N	f	f
2087	COST_CENTER	Cost Center	Feedspan	10063	2022-09-20 08:39:10.403312+00	2022-09-20 08:39:10.40334+00	1	\N	\N	f	f
2088	COST_CENTER	Cost Center	Fido Solutions	10064	2022-09-20 08:39:10.403535+00	2022-09-20 08:39:10.403564+00	1	\N	\N	f	f
2089	COST_CENTER	Cost Center	Finscent	10065	2022-09-20 08:39:10.40362+00	2022-09-20 08:39:10.403647+00	1	\N	\N	f	f
2090	COST_CENTER	Cost Center	First Air	10066	2022-09-20 08:39:10.403704+00	2022-09-20 08:39:10.403731+00	1	\N	\N	f	f
2091	COST_CENTER	Cost Center	First National Bank	10067	2022-09-20 08:39:10.403788+00	2022-09-20 08:39:10.403815+00	1	\N	\N	f	f
2092	COST_CENTER	Cost Center	First Rand	10068	2022-09-20 08:39:10.403872+00	2022-09-20 08:39:10.403899+00	1	\N	\N	f	f
2093	COST_CENTER	Cost Center	Flashdog	10069	2022-09-20 08:39:10.403955+00	2022-09-20 08:39:10.403982+00	1	\N	\N	f	f
2094	COST_CENTER	Cost Center	Flickr	10070	2022-09-20 08:39:10.404039+00	2022-09-20 08:39:10.404066+00	1	\N	\N	f	f
2095	COST_CENTER	Cost Center	FNB Connect	10071	2022-09-20 08:39:10.404123+00	2022-09-20 08:39:10.40415+00	1	\N	\N	f	f
2096	COST_CENTER	Cost Center	Focus Med	10072	2022-09-20 08:39:10.404207+00	2022-09-20 08:39:10.404234+00	1	\N	\N	f	f
2097	COST_CENTER	Cost Center	Food Lover's Market	10073	2022-09-20 08:39:10.40429+00	2022-09-20 08:39:10.404317+00	1	\N	\N	f	f
2098	COST_CENTER	Cost Center	Ford Motor Company of Canada	10074	2022-09-20 08:39:10.404496+00	2022-09-20 08:39:10.404535+00	1	\N	\N	f	f
2099	COST_CENTER	Cost Center	Four Seasons Hotels and Resorts	10075	2022-09-20 08:39:10.404593+00	2022-09-20 08:39:10.40462+00	1	\N	\N	f	f
2100	COST_CENTER	Cost Center	Freedom Mobile	10076	2022-09-20 08:39:10.404677+00	2022-09-20 08:39:10.404704+00	1	\N	\N	f	f
2101	COST_CENTER	Cost Center	Fuji Air	10077	2022-09-20 08:39:10.40476+00	2022-09-20 08:39:10.404788+00	1	\N	\N	f	f
2102	COST_CENTER	Cost Center	Gadgetron	10078	2022-09-20 08:39:10.404845+00	2022-09-20 08:39:10.404872+00	1	\N	\N	f	f
2103	COST_CENTER	Cost Center	Gallo Record Company	10079	2022-09-20 08:39:10.404928+00	2022-09-20 08:39:10.404956+00	1	\N	\N	f	f
2104	COST_CENTER	Cost Center	GBD Inc	10080	2022-09-20 08:39:10.405012+00	2022-09-20 08:39:10.405039+00	1	\N	\N	f	f
2105	COST_CENTER	Cost Center	Gemini Manufacturing Services	10081	2022-09-20 08:39:10.405096+00	2022-09-20 08:39:10.405123+00	1	\N	\N	f	f
2106	COST_CENTER	Cost Center	Genentech, Inc.	10082	2022-09-20 08:39:10.405179+00	2022-09-20 08:39:10.405206+00	1	\N	\N	f	f
2107	COST_CENTER	Cost Center	Georgia Power Company	10083	2022-09-20 08:39:10.405262+00	2022-09-20 08:39:10.405289+00	1	\N	\N	f	f
2108	COST_CENTER	Cost Center	Gijima Group	10084	2022-09-20 08:39:10.405345+00	2022-09-20 08:39:10.405494+00	1	\N	\N	f	f
2109	COST_CENTER	Cost Center	Gilead Sciences	10085	2022-09-20 08:39:10.405563+00	2022-09-20 08:39:10.405591+00	1	\N	\N	f	f
2110	COST_CENTER	Cost Center	Global Dynamics	10086	2022-09-20 08:39:10.405648+00	2022-09-20 08:39:10.405675+00	1	\N	\N	f	f
2111	COST_CENTER	Cost Center	Global Manufacturing	10087	2022-09-20 08:39:10.405731+00	2022-09-20 08:39:10.405759+00	1	\N	\N	f	f
2112	COST_CENTER	Cost Center	Globochem	10088	2022-09-20 08:39:10.405815+00	2022-09-20 08:39:10.405842+00	1	\N	\N	f	f
2113	COST_CENTER	Cost Center	Golden Arrow Bus Services	10089	2022-09-20 08:39:10.405898+00	2022-09-20 08:39:10.405925+00	1	\N	\N	f	f
2114	COST_CENTER	Cost Center	Gold Fields	10090	2022-09-20 08:39:10.405981+00	2022-09-20 08:39:10.406009+00	1	\N	\N	f	f
2115	COST_CENTER	Cost Center	Grand Trunk Semaphore	10091	2022-09-20 08:39:10.406065+00	2022-09-20 08:39:10.406092+00	1	\N	\N	f	f
2116	COST_CENTER	Cost Center	Grayson Sky Domes	10092	2022-09-20 08:39:10.406148+00	2022-09-20 08:39:10.406176+00	1	\N	\N	f	f
2117	COST_CENTER	Cost Center	GSATi	10093	2022-09-20 08:39:10.406232+00	2022-09-20 08:39:10.40626+00	1	\N	\N	f	f
2118	COST_CENTER	Cost Center	GS Industries	10094	2022-09-20 08:39:10.406316+00	2022-09-20 08:39:10.406343+00	1	\N	\N	f	f
2119	COST_CENTER	Cost Center	Gulf States Paper Corporation	10095	2022-09-20 08:39:10.406528+00	2022-09-20 08:39:10.406569+00	1	\N	\N	f	f
2120	COST_CENTER	Cost Center	Hanso Foundation	10096	2022-09-20 08:39:10.406648+00	2022-09-20 08:39:10.406676+00	1	\N	\N	f	f
2121	COST_CENTER	Cost Center	Harmony Gold	10097	2022-09-20 08:39:10.406733+00	2022-09-20 08:39:10.406761+00	1	\N	\N	f	f
2122	COST_CENTER	Cost Center	Heart and Vascular Clinic	10098	2022-09-20 08:39:10.406817+00	2022-09-20 08:39:10.406844+00	1	\N	\N	f	f
2123	COST_CENTER	Cost Center	Hishii Industries	10099	2022-09-20 08:39:10.4069+00	2022-09-20 08:39:10.406927+00	1	\N	\N	f	f
2124	COST_CENTER	Cost Center	Hollard Group	10100	2022-09-20 08:39:10.413482+00	2022-09-20 08:39:10.413523+00	1	\N	\N	f	f
2125	COST_CENTER	Cost Center	Illovo Sugar	10101	2022-09-20 08:39:10.41359+00	2022-09-20 08:39:10.413619+00	1	\N	\N	f	f
2126	COST_CENTER	Cost Center	Impala Platinum	10102	2022-09-20 08:39:10.413678+00	2022-09-20 08:39:10.413706+00	1	\N	\N	f	f
2127	COST_CENTER	Cost Center	InGen	10103	2022-09-20 08:39:10.413764+00	2022-09-20 08:39:10.413792+00	1	\N	\N	f	f
2128	COST_CENTER	Cost Center	Innova Solutions	10104	2022-09-20 08:39:10.41385+00	2022-09-20 08:39:10.413877+00	1	\N	\N	f	f
2129	COST_CENTER	Cost Center	Innovation Arch	10105	2022-09-20 08:39:10.413934+00	2022-09-20 08:39:10.413961+00	1	\N	\N	f	f
2130	COST_CENTER	Cost Center	Insurance Megacorp	10106	2022-09-20 08:39:10.414018+00	2022-09-20 08:39:10.414045+00	1	\N	\N	f	f
2131	COST_CENTER	Cost Center	Intelligent Audit	10107	2022-09-20 08:39:10.414102+00	2022-09-20 08:39:10.414129+00	1	\N	\N	f	f
2132	COST_CENTER	Cost Center	Interplanetary Expeditions	10108	2022-09-20 08:39:10.414186+00	2022-09-20 08:39:10.414213+00	1	\N	\N	f	f
2133	COST_CENTER	Cost Center	Intrepid Minerals Corporation	10109	2022-09-20 08:39:10.41427+00	2022-09-20 08:39:10.414297+00	1	\N	\N	f	f
2134	COST_CENTER	Cost Center	Investec	10110	2022-09-20 08:39:10.414353+00	2022-09-20 08:39:10.41438+00	1	\N	\N	f	f
2135	COST_CENTER	Cost Center	IPS	10111	2022-09-20 08:39:10.414568+00	2022-09-20 08:39:10.414607+00	1	\N	\N	f	f
2136	COST_CENTER	Cost Center	Itex	10112	2022-09-20 08:39:10.414663+00	2022-09-20 08:39:10.41469+00	1	\N	\N	f	f
2138	COST_CENTER	Cost Center	Izon	10114	2022-09-20 08:39:10.414829+00	2022-09-20 08:39:10.414856+00	1	\N	\N	f	f
2139	COST_CENTER	Cost Center	Jabberstorm	10115	2022-09-20 08:39:10.414912+00	2022-09-20 08:39:10.414939+00	1	\N	\N	f	f
2140	COST_CENTER	Cost Center	Jabbertype	10116	2022-09-20 08:39:10.414995+00	2022-09-20 08:39:10.415022+00	1	\N	\N	f	f
2141	COST_CENTER	Cost Center	James Mintz Group, Inc.	10117	2022-09-20 08:39:10.415078+00	2022-09-20 08:39:10.415105+00	1	\N	\N	f	f
2142	COST_CENTER	Cost Center	Jaxnation	10118	2022-09-20 08:39:10.415161+00	2022-09-20 08:39:10.415188+00	1	\N	\N	f	f
2143	COST_CENTER	Cost Center	Jazzy	10119	2022-09-20 08:39:10.415244+00	2022-09-20 08:39:10.415271+00	1	\N	\N	f	f
2144	COST_CENTER	Cost Center	Junk Mail Digital Media	10120	2022-09-20 08:39:10.415326+00	2022-09-20 08:39:10.415458+00	1	\N	\N	f	f
2145	COST_CENTER	Cost Center	Kansas City Power and Light Co.	10121	2022-09-20 08:39:10.415515+00	2022-09-20 08:39:10.415543+00	1	\N	\N	f	f
2146	COST_CENTER	Cost Center	Kazio	10122	2022-09-20 08:39:10.415599+00	2022-09-20 08:39:10.415627+00	1	\N	\N	f	f
2147	COST_CENTER	Cost Center	KENTECH Consulting	10123	2022-09-20 08:39:10.415683+00	2022-09-20 08:39:10.41571+00	1	\N	\N	f	f
2148	COST_CENTER	Cost Center	Khumalo	10124	2022-09-20 08:39:10.415765+00	2022-09-20 08:39:10.415792+00	1	\N	\N	f	f
2149	COST_CENTER	Cost Center	Klondike Gold Corporation	10125	2022-09-20 08:39:10.415849+00	2022-09-20 08:39:10.415876+00	1	\N	\N	f	f
2150	COST_CENTER	Cost Center	Kumba Iron Ore	10126	2022-09-20 08:39:10.415942+00	2022-09-20 08:39:10.415969+00	1	\N	\N	f	f
2151	COST_CENTER	Cost Center	Kwik-E-Mart	10127	2022-09-20 08:39:10.416026+00	2022-09-20 08:39:10.416053+00	1	\N	\N	f	f
2152	COST_CENTER	Cost Center	Kwilith	10128	2022-09-20 08:39:10.416109+00	2022-09-20 08:39:10.416136+00	1	\N	\N	f	f
2153	COST_CENTER	Cost Center	Leexo	10129	2022-09-20 08:39:10.416193+00	2022-09-20 08:39:10.416232+00	1	\N	\N	f	f
2154	COST_CENTER	Cost Center	Leo A. Daly Company	10130	2022-09-20 08:39:10.416512+00	2022-09-20 08:39:10.416658+00	1	\N	\N	f	f
2155	COST_CENTER	Cost Center	LexCorp	10131	2022-09-20 08:39:10.416718+00	2022-09-20 08:39:10.416745+00	1	\N	\N	f	f
2156	COST_CENTER	Cost Center	Liandri Mining	10132	2022-09-20 08:39:10.416802+00	2022-09-20 08:39:10.41683+00	1	\N	\N	f	f
2157	COST_CENTER	Cost Center	LIFE Healthcare Group	10133	2022-09-20 08:39:10.416886+00	2022-09-20 08:39:10.416913+00	1	\N	\N	f	f
2158	COST_CENTER	Cost Center	Linkbuzz	10134	2022-09-20 08:39:10.416969+00	2022-09-20 08:39:10.416997+00	1	\N	\N	f	f
2159	COST_CENTER	Cost Center	Livefish	10135	2022-09-20 08:39:10.417053+00	2022-09-20 08:39:10.417081+00	1	\N	\N	f	f
2160	COST_CENTER	Cost Center	Livetube	10136	2022-09-20 08:39:10.417137+00	2022-09-20 08:39:10.417165+00	1	\N	\N	f	f
2161	COST_CENTER	Cost Center	Live With Intention	10137	2022-09-20 08:39:10.417221+00	2022-09-20 08:39:10.417248+00	1	\N	\N	f	f
2162	COST_CENTER	Cost Center	Mathews and Associates Architects	10138	2022-09-20 08:39:10.417305+00	2022-09-20 08:39:10.417347+00	1	\N	\N	f	f
2163	COST_CENTER	Cost Center	Matrox Electronic Systems Ltd.	10139	2022-09-20 08:39:10.417522+00	2022-09-20 08:39:10.41755+00	1	\N	\N	f	f
2164	COST_CENTER	Cost Center	Matsumura Fishworks	10140	2022-09-20 08:39:10.417607+00	2022-09-20 08:39:10.417634+00	1	\N	\N	f	f
2165	COST_CENTER	Cost Center	McCandless Communications	10141	2022-09-20 08:39:10.41769+00	2022-09-20 08:39:10.417718+00	1	\N	\N	f	f
2166	COST_CENTER	Cost Center	Med dot	10142	2022-09-20 08:39:10.417774+00	2022-09-20 08:39:10.417801+00	1	\N	\N	f	f
2167	COST_CENTER	Cost Center	Medical Mechanica	10143	2022-09-20 08:39:10.417858+00	2022-09-20 08:39:10.417885+00	1	\N	\N	f	f
2168	COST_CENTER	Cost Center	Medical Research Technologies	10144	2022-09-20 08:39:10.417941+00	2022-09-20 08:39:10.417968+00	1	\N	\N	f	f
2169	COST_CENTER	Cost Center	Mediclinic International	10145	2022-09-20 08:39:10.418024+00	2022-09-20 08:39:10.418052+00	1	\N	\N	f	f
2170	COST_CENTER	Cost Center	Mega Lo Mart	10146	2022-09-20 08:39:10.418108+00	2022-09-20 08:39:10.418135+00	1	\N	\N	f	f
2171	COST_CENTER	Cost Center	Mensa, Ltd.	10147	2022-09-20 08:39:10.418192+00	2022-09-20 08:39:10.41822+00	1	\N	\N	f	f
2172	COST_CENTER	Cost Center	Metacortex	10148	2022-09-20 08:39:10.418276+00	2022-09-20 08:39:10.418304+00	1	\N	\N	f	f
2173	COST_CENTER	Cost Center	Miboo	10149	2022-09-20 08:39:10.418372+00	2022-09-20 08:39:10.418486+00	1	\N	\N	f	f
2174	COST_CENTER	Cost Center	Mishima Zaibatsu	10150	2022-09-20 08:39:10.426011+00	2022-09-20 08:39:10.426058+00	1	\N	\N	f	f
2175	COST_CENTER	Cost Center	MK Manufacturing	10151	2022-09-20 08:39:10.426144+00	2022-09-20 08:39:10.426177+00	1	\N	\N	f	f
2176	COST_CENTER	Cost Center	M-Net	10152	2022-09-20 08:39:10.426249+00	2022-09-20 08:39:10.426288+00	1	\N	\N	f	f
2177	COST_CENTER	Cost Center	Monsters, Inc.	10153	2022-09-20 08:39:10.426527+00	2022-09-20 08:39:10.426561+00	1	\N	\N	f	f
2178	COST_CENTER	Cost Center	Mr. Price Group Ltd.	10154	2022-09-20 08:39:10.426631+00	2022-09-20 08:39:10.426661+00	1	\N	\N	f	f
2179	COST_CENTER	Cost Center	MTN Group	10155	2022-09-20 08:39:10.426732+00	2022-09-20 08:39:10.426761+00	1	\N	\N	f	f
2180	COST_CENTER	Cost Center	MultiChoice	10156	2022-09-20 08:39:10.426952+00	2022-09-20 08:39:10.427028+00	1	\N	\N	f	f
2181	COST_CENTER	Cost Center	MWEB	10157	2022-09-20 08:39:10.427297+00	2022-09-20 08:39:10.427543+00	1	\N	\N	f	f
2182	COST_CENTER	Cost Center	Mybuzz	10158	2022-09-20 08:39:10.427918+00	2022-09-20 08:39:10.427967+00	1	\N	\N	f	f
2183	COST_CENTER	Cost Center	Myworks	10159	2022-09-20 08:39:10.428056+00	2022-09-20 08:39:10.428118+00	1	\N	\N	f	f
2184	COST_CENTER	Cost Center	Nakatomi Corporation	10160	2022-09-20 08:39:10.4294+00	2022-09-20 08:39:10.429452+00	1	\N	\N	f	f
2185	COST_CENTER	Cost Center	Nanocell	10161	2022-09-20 08:39:10.429525+00	2022-09-20 08:39:10.429554+00	1	\N	\N	f	f
2186	COST_CENTER	Cost Center	Naples Pediatrics	10162	2022-09-20 08:39:10.429614+00	2022-09-20 08:39:10.429642+00	1	\N	\N	f	f
2187	COST_CENTER	Cost Center	Naspers	10163	2022-09-20 08:39:10.429701+00	2022-09-20 08:39:10.429728+00	1	\N	\N	f	f
2188	COST_CENTER	Cost Center	National Clean Energy	10164	2022-09-20 08:39:10.429785+00	2022-09-20 08:39:10.429812+00	1	\N	\N	f	f
2189	COST_CENTER	Cost Center	Nedbank	10165	2022-09-20 08:39:10.42987+00	2022-09-20 08:39:10.429897+00	1	\N	\N	f	f
2190	COST_CENTER	Cost Center	Neotel	10166	2022-09-20 08:39:10.429954+00	2022-09-20 08:39:10.429981+00	1	\N	\N	f	f
2191	COST_CENTER	Cost Center	Neoveo	10167	2022-09-20 08:39:10.430038+00	2022-09-20 08:39:10.430065+00	1	\N	\N	f	f
2192	COST_CENTER	Cost Center	N.E.R.D.	10168	2022-09-20 08:39:10.430122+00	2022-09-20 08:39:10.43015+00	1	\N	\N	f	f
2193	COST_CENTER	Cost Center	Netcare	10169	2022-09-20 08:39:10.430207+00	2022-09-20 08:39:10.430234+00	1	\N	\N	f	f
2194	COST_CENTER	Cost Center	Network23	10170	2022-09-20 08:39:10.43029+00	2022-09-20 08:39:10.430318+00	1	\N	\N	f	f
2195	COST_CENTER	Cost Center	new customer	10171	2022-09-20 08:39:10.430374+00	2022-09-20 08:39:10.430416+00	1	\N	\N	f	f
2196	COST_CENTER	Cost Center	News Day	10172	2022-09-20 08:39:10.430615+00	2022-09-20 08:39:10.430653+00	1	\N	\N	f	f
2197	COST_CENTER	Cost Center	Nirvana	10173	2022-09-20 08:39:10.430758+00	2022-09-20 08:39:10.430788+00	1	\N	\N	f	f
2198	COST_CENTER	Cost Center	Nordyne Defense	10174	2022-09-20 08:39:10.430849+00	2022-09-20 08:39:10.430888+00	1	\N	\N	f	f
2199	COST_CENTER	Cost Center	NorthAm Robotics	10175	2022-09-20 08:39:10.430946+00	2022-09-20 08:39:10.430973+00	1	\N	\N	f	f
2200	COST_CENTER	Cost Center	North Central Positronics	10176	2022-09-20 08:39:10.43103+00	2022-09-20 08:39:10.431057+00	1	\N	\N	f	f
2201	COST_CENTER	Cost Center	Novamed	10177	2022-09-20 08:39:10.431114+00	2022-09-20 08:39:10.431141+00	1	\N	\N	f	f
2202	COST_CENTER	Cost Center	Npath	10178	2022-09-20 08:39:10.431197+00	2022-09-20 08:39:10.431225+00	1	\N	\N	f	f
2203	COST_CENTER	Cost Center	Oakland County Community Mental Health	10179	2022-09-20 08:39:10.431281+00	2022-09-20 08:39:10.431308+00	1	\N	\N	f	f
2204	COST_CENTER	Cost Center	Old Mutual	10180	2022-09-20 08:39:10.431489+00	2022-09-20 08:39:10.43153+00	1	\N	\N	f	f
2205	COST_CENTER	Cost Center	Olin Corporation	10181	2022-09-20 08:39:10.431588+00	2022-09-20 08:39:10.431615+00	1	\N	\N	f	f
2206	COST_CENTER	Cost Center	Omni Consumer Products	10182	2022-09-20 08:39:10.431672+00	2022-09-20 08:39:10.431699+00	1	\N	\N	f	f
2207	COST_CENTER	Cost Center	Oncolytics Biotech Inc.	10183	2022-09-20 08:39:10.431755+00	2022-09-20 08:39:10.431783+00	1	\N	\N	f	f
2208	COST_CENTER	Cost Center	Optican	10184	2022-09-20 08:39:10.431838+00	2022-09-20 08:39:10.431866+00	1	\N	\N	f	f
2209	COST_CENTER	Cost Center	Orchard Group	10185	2022-09-20 08:39:10.431922+00	2022-09-20 08:39:10.431949+00	1	\N	\N	f	f
2210	COST_CENTER	Cost Center	OsCorp	10186	2022-09-20 08:39:10.432006+00	2022-09-20 08:39:10.432033+00	1	\N	\N	f	f
2211	COST_CENTER	Cost Center	Ovi	10187	2022-09-20 08:39:10.432089+00	2022-09-20 08:39:10.432116+00	1	\N	\N	f	f
2212	COST_CENTER	Cost Center	Pacificare Health Systems Az	10188	2022-09-20 08:39:10.432173+00	2022-09-20 08:39:10.4322+00	1	\N	\N	f	f
2213	COST_CENTER	Cost Center	Pacificorp	10189	2022-09-20 08:39:10.432255+00	2022-09-20 08:39:10.432282+00	1	\N	\N	f	f
2214	COST_CENTER	Cost Center	PA Neurosurgery and Neuroscience	10190	2022-09-20 08:39:10.432338+00	2022-09-20 08:39:10.432511+00	1	\N	\N	f	f
2215	COST_CENTER	Cost Center	Paper Street Soap Co.	10191	2022-09-20 08:39:10.432599+00	2022-09-20 08:39:10.432627+00	1	\N	\N	f	f
2216	COST_CENTER	Cost Center	Parrish Communications	10192	2022-09-20 08:39:10.432683+00	2022-09-20 08:39:10.432711+00	1	\N	\N	f	f
2217	COST_CENTER	Cost Center	Pediatric Subspecialty Faculty	10193	2022-09-20 08:39:10.432767+00	2022-09-20 08:39:10.432794+00	1	\N	\N	f	f
2218	COST_CENTER	Cost Center	Photofeed	10194	2022-09-20 08:39:10.43285+00	2022-09-20 08:39:10.432877+00	1	\N	\N	f	f
2219	COST_CENTER	Cost Center	Photojam	10195	2022-09-20 08:39:10.432933+00	2022-09-20 08:39:10.43296+00	1	\N	\N	f	f
2220	COST_CENTER	Cost Center	Pick 'n Pay	10196	2022-09-20 08:39:10.433016+00	2022-09-20 08:39:10.433044+00	1	\N	\N	f	f
2221	COST_CENTER	Cost Center	Piggly Wiggly Carolina Co.	10197	2022-09-20 08:39:10.4331+00	2022-09-20 08:39:10.433127+00	1	\N	\N	f	f
2222	COST_CENTER	Cost Center	Pioneer Foods	10198	2022-09-20 08:39:10.433183+00	2022-09-20 08:39:10.43321+00	1	\N	\N	f	f
2223	COST_CENTER	Cost Center	Pixonyx	10199	2022-09-20 08:39:10.433267+00	2022-09-20 08:39:10.433294+00	1	\N	\N	f	f
2224	COST_CENTER	Cost Center	Porter Technologies	10200	2022-09-20 08:39:10.438749+00	2022-09-20 08:39:10.438792+00	1	\N	\N	f	f
2225	COST_CENTER	Cost Center	33Across	9806	2022-09-20 08:39:10.438859+00	2022-09-20 08:39:10.438888+00	1	\N	\N	f	f
2226	COST_CENTER	Cost Center	3Way International Logistics	9807	2022-09-20 08:39:10.438947+00	2022-09-20 08:39:10.438975+00	1	\N	\N	f	f
2227	COST_CENTER	Cost Center	ABB Grain	9808	2022-09-20 08:39:10.439032+00	2022-09-20 08:39:10.43906+00	1	\N	\N	f	f
2228	COST_CENTER	Cost Center	ABC Learning	9809	2022-09-20 08:39:10.439118+00	2022-09-20 08:39:10.439145+00	1	\N	\N	f	f
2229	COST_CENTER	Cost Center	ABSA Group	9810	2022-09-20 08:39:10.439203+00	2022-09-20 08:39:10.439231+00	1	\N	\N	f	f
2230	COST_CENTER	Cost Center	AB SQUARE	9811	2022-09-20 08:39:10.439289+00	2022-09-20 08:39:10.439317+00	1	\N	\N	f	f
2231	COST_CENTER	Cost Center	Abstergo Industries	9812	2022-09-20 08:39:10.439374+00	2022-09-20 08:39:10.439402+00	1	\N	\N	f	f
2232	COST_CENTER	Cost Center	Ace Tomato	9813	2022-09-20 08:39:10.439613+00	2022-09-20 08:39:10.439641+00	1	\N	\N	f	f
2233	COST_CENTER	Cost Center	Ache Records	9814	2022-09-20 08:39:10.439699+00	2022-09-20 08:39:10.439726+00	1	\N	\N	f	f
2234	COST_CENTER	Cost Center	Acme	9815	2022-09-20 08:39:10.439783+00	2022-09-20 08:39:10.43981+00	1	\N	\N	f	f
2235	COST_CENTER	Cost Center	ACSA	9816	2022-09-20 08:39:10.439867+00	2022-09-20 08:39:10.439894+00	1	\N	\N	f	f
2236	COST_CENTER	Cost Center	Adam Internet	9817	2022-09-20 08:39:10.43995+00	2022-09-20 08:39:10.439978+00	1	\N	\N	f	f
2237	COST_CENTER	Cost Center	Adcock Ingram	9818	2022-09-20 08:39:10.440034+00	2022-09-20 08:39:10.440061+00	1	\N	\N	f	f
2238	COST_CENTER	Cost Center	Admire Arts	9819	2022-09-20 08:39:10.440118+00	2022-09-20 08:39:10.440145+00	1	\N	\N	f	f
2239	COST_CENTER	Cost Center	Advanced Cyclotron Systems	9820	2022-09-20 08:39:10.440202+00	2022-09-20 08:39:10.440229+00	1	\N	\N	f	f
2240	COST_CENTER	Cost Center	Aerosonde Ltd	9821	2022-09-20 08:39:10.440285+00	2022-09-20 08:39:10.440312+00	1	\N	\N	f	f
2241	COST_CENTER	Cost Center	Afrihost	9822	2022-09-20 08:39:10.44064+00	2022-09-20 08:39:10.440663+00	1	\N	\N	f	f
2242	COST_CENTER	Cost Center	AG Insurance	9823	2022-09-20 08:39:10.440824+00	2022-09-20 08:39:10.440852+00	1	\N	\N	f	f
2243	COST_CENTER	Cost Center	Aimbu	9824	2022-09-20 08:39:10.440909+00	2022-09-20 08:39:10.440936+00	1	\N	\N	f	f
2244	COST_CENTER	Cost Center	Ajax	9825	2022-09-20 08:39:10.440993+00	2022-09-20 08:39:10.44102+00	1	\N	\N	f	f
2245	COST_CENTER	Cost Center	Ajira Airways	9826	2022-09-20 08:39:10.441076+00	2022-09-20 08:39:10.441103+00	1	\N	\N	f	f
2246	COST_CENTER	Cost Center	Aldo Group	9827	2022-09-20 08:39:10.441159+00	2022-09-20 08:39:10.441186+00	1	\N	\N	f	f
2247	COST_CENTER	Cost Center	Algonquin Power and Utilities	9828	2022-09-20 08:39:10.441242+00	2022-09-20 08:39:10.441269+00	1	\N	\N	f	f
2248	COST_CENTER	Cost Center	Alinta Gas	9829	2022-09-20 08:39:10.441457+00	2022-09-20 08:39:10.441496+00	1	\N	\N	f	f
2249	COST_CENTER	Cost Center	Allied British Plastics	9830	2022-09-20 08:39:10.441552+00	2022-09-20 08:39:10.44158+00	1	\N	\N	f	f
2250	COST_CENTER	Cost Center	Allphones	9831	2022-09-20 08:39:10.441637+00	2022-09-20 08:39:10.441664+00	1	\N	\N	f	f
2251	COST_CENTER	Cost Center	Alumina	9832	2022-09-20 08:39:10.44172+00	2022-09-20 08:39:10.441747+00	1	\N	\N	f	f
2252	COST_CENTER	Cost Center	Amcor	9833	2022-09-20 08:39:10.441804+00	2022-09-20 08:39:10.441831+00	1	\N	\N	f	f
2253	COST_CENTER	Cost Center	ANCA	9834	2022-09-20 08:39:10.441887+00	2022-09-20 08:39:10.441914+00	1	\N	\N	f	f
2254	COST_CENTER	Cost Center	Anglo American	9835	2022-09-20 08:39:10.441988+00	2022-09-20 08:39:10.442017+00	1	\N	\N	f	f
2255	COST_CENTER	Cost Center	Anglo American Platinum	9836	2022-09-20 08:39:10.442081+00	2022-09-20 08:39:10.442111+00	1	\N	\N	f	f
2256	COST_CENTER	Cost Center	Angoss	9837	2022-09-20 08:39:10.442176+00	2022-09-20 08:39:10.442206+00	1	\N	\N	f	f
2257	COST_CENTER	Cost Center	Angus and Robertson	9838	2022-09-20 08:39:10.442267+00	2022-09-20 08:39:10.442296+00	1	\N	\N	f	f
2258	COST_CENTER	Cost Center	Ansell	9839	2022-09-20 08:39:10.442482+00	2022-09-20 08:39:10.44251+00	1	\N	\N	f	f
2259	COST_CENTER	Cost Center	Aperture Science	9840	2022-09-20 08:39:10.442567+00	2022-09-20 08:39:10.442594+00	1	\N	\N	f	f
2260	COST_CENTER	Cost Center	Appliances Online	9841	2022-09-20 08:39:10.442651+00	2022-09-20 08:39:10.442678+00	1	\N	\N	f	f
2261	COST_CENTER	Cost Center	Applied Biomics	9842	2022-09-20 08:39:10.442735+00	2022-09-20 08:39:10.442762+00	1	\N	\N	f	f
2262	COST_CENTER	Cost Center	Appnovation	9843	2022-09-20 08:39:10.442817+00	2022-09-20 08:39:10.442844+00	1	\N	\N	f	f
2263	COST_CENTER	Cost Center	Arbitration Association	9844	2022-09-20 08:39:10.442901+00	2022-09-20 08:39:10.442928+00	1	\N	\N	f	f
2264	COST_CENTER	Cost Center	ARCAM Corporation	9845	2022-09-20 08:39:10.442984+00	2022-09-20 08:39:10.443011+00	1	\N	\N	f	f
105	CATEGORY	Category	buh	184631	2022-09-20 08:39:03.37368+00	2022-09-20 08:39:03.373712+00	1	t	\N	f	f
2265	COST_CENTER	Cost Center	Aristocrat Leisure	9846	2022-09-20 08:39:10.443068+00	2022-09-20 08:39:10.443095+00	1	\N	\N	f	f
2266	COST_CENTER	Cost Center	Arkansas Blue Cross and Blue Shield	9847	2022-09-20 08:39:10.443152+00	2022-09-20 08:39:10.443179+00	1	\N	\N	f	f
2267	COST_CENTER	Cost Center	Army and Navy Stores	9848	2022-09-20 08:39:10.443235+00	2022-09-20 08:39:10.443263+00	1	\N	\N	f	f
2268	COST_CENTER	Cost Center	Arnott's Biscuits	9849	2022-09-20 08:39:10.443319+00	2022-09-20 08:39:10.443346+00	1	\N	\N	f	f
2269	COST_CENTER	Cost Center	Arrow Research Corporation	9850	2022-09-20 08:39:10.443542+00	2022-09-20 08:39:10.443571+00	1	\N	\N	f	f
2270	COST_CENTER	Cost Center	Aspen Pharmacare	9851	2022-09-20 08:39:10.443627+00	2022-09-20 08:39:10.443655+00	1	\N	\N	f	f
2271	COST_CENTER	Cost Center	Astromech	9852	2022-09-20 08:39:10.443712+00	2022-09-20 08:39:10.443739+00	1	\N	\N	f	f
2272	COST_CENTER	Cost Center	ATB Financial	9853	2022-09-20 08:39:10.443795+00	2022-09-20 08:39:10.443823+00	1	\N	\N	f	f
2273	COST_CENTER	Cost Center	Atlanta Integrative Medicine	9854	2022-09-20 08:39:10.443879+00	2022-09-20 08:39:10.443906+00	1	\N	\N	f	f
2274	COST_CENTER	Cost Center	Atlassian	9855	2022-09-20 08:39:10.450916+00	2022-09-20 08:39:10.450958+00	1	\N	\N	f	f
2275	COST_CENTER	Cost Center	Augusta Medical Associates	9856	2022-09-20 08:39:10.451027+00	2022-09-20 08:39:10.451056+00	1	\N	\N	f	f
2276	COST_CENTER	Cost Center	Aussie Broadband	9857	2022-09-20 08:39:10.451116+00	2022-09-20 08:39:10.451144+00	1	\N	\N	f	f
2277	COST_CENTER	Cost Center	Austal Ships	9858	2022-09-20 08:39:10.451202+00	2022-09-20 08:39:10.45123+00	1	\N	\N	f	f
2278	COST_CENTER	Cost Center	Austereo	9859	2022-09-20 08:39:10.451286+00	2022-09-20 08:39:10.451313+00	1	\N	\N	f	f
2279	COST_CENTER	Cost Center	Australia and New Zealand Banking Group (ANZ)	9860	2022-09-20 08:39:10.451497+00	2022-09-20 08:39:10.45153+00	1	\N	\N	f	f
2280	COST_CENTER	Cost Center	Australian Agricultural Company	9861	2022-09-20 08:39:10.451601+00	2022-09-20 08:39:10.451629+00	1	\N	\N	f	f
2281	COST_CENTER	Cost Center	Australian airExpress	9862	2022-09-20 08:39:10.451686+00	2022-09-20 08:39:10.451714+00	1	\N	\N	f	f
2282	COST_CENTER	Cost Center	Australian Broadcasting Corporation	9863	2022-09-20 08:39:10.451771+00	2022-09-20 08:39:10.451798+00	1	\N	\N	f	f
2283	COST_CENTER	Cost Center	Australian Defence Industries	9864	2022-09-20 08:39:10.451855+00	2022-09-20 08:39:10.451882+00	1	\N	\N	f	f
2284	COST_CENTER	Cost Center	Australian Gas Light Company	9865	2022-09-20 08:39:10.451938+00	2022-09-20 08:39:10.451965+00	1	\N	\N	f	f
2285	COST_CENTER	Cost Center	Australian Motor Industries (AMI)	9866	2022-09-20 08:39:10.452021+00	2022-09-20 08:39:10.452048+00	1	\N	\N	f	f
2286	COST_CENTER	Cost Center	Australian Railroad Group	9867	2022-09-20 08:39:10.452105+00	2022-09-20 08:39:10.452132+00	1	\N	\N	f	f
2287	COST_CENTER	Cost Center	Australian Securities Exchange	9868	2022-09-20 08:39:10.452188+00	2022-09-20 08:39:10.452215+00	1	\N	\N	f	f
2288	COST_CENTER	Cost Center	Ausway	9869	2022-09-20 08:39:10.452272+00	2022-09-20 08:39:10.452299+00	1	\N	\N	f	f
2289	COST_CENTER	Cost Center	Automobile Association of South Africa	9870	2022-09-20 08:39:10.452366+00	2022-09-20 08:39:10.452487+00	1	\N	\N	f	f
2290	COST_CENTER	Cost Center	Avaveo	9871	2022-09-20 08:39:10.452559+00	2022-09-20 08:39:10.452587+00	1	\N	\N	f	f
2291	COST_CENTER	Cost Center	Avu	9872	2022-09-20 08:39:10.452644+00	2022-09-20 08:39:10.452671+00	1	\N	\N	f	f
2292	COST_CENTER	Cost Center	AWB Limited	9873	2022-09-20 08:39:10.452728+00	2022-09-20 08:39:10.452756+00	1	\N	\N	f	f
2293	COST_CENTER	Cost Center	BAE Systems Australia	9874	2022-09-20 08:39:10.452812+00	2022-09-20 08:39:10.45284+00	1	\N	\N	f	f
2294	COST_CENTER	Cost Center	Bakers Delight	9875	2022-09-20 08:39:10.452897+00	2022-09-20 08:39:10.452924+00	1	\N	\N	f	f
2295	COST_CENTER	Cost Center	Banff Lodging Co	9876	2022-09-20 08:39:10.45298+00	2022-09-20 08:39:10.453008+00	1	\N	\N	f	f
2296	COST_CENTER	Cost Center	Bard Ventures	9877	2022-09-20 08:39:10.453064+00	2022-09-20 08:39:10.453092+00	1	\N	\N	f	f
2297	COST_CENTER	Cost Center	Bayer Corporation	9878	2022-09-20 08:39:10.453148+00	2022-09-20 08:39:10.453175+00	1	\N	\N	f	f
2298	COST_CENTER	Cost Center	BC Research	9879	2022-09-20 08:39:10.453232+00	2022-09-20 08:39:10.453259+00	1	\N	\N	f	f
2299	COST_CENTER	Cost Center	Beaurepaires	9880	2022-09-20 08:39:10.453315+00	2022-09-20 08:39:10.453343+00	1	\N	\N	f	f
2300	COST_CENTER	Cost Center	Becker Entertainment	9881	2022-09-20 08:39:10.45353+00	2022-09-20 08:39:10.453555+00	1	\N	\N	f	f
2301	COST_CENTER	Cost Center	Been Verified	9882	2022-09-20 08:39:10.453607+00	2022-09-20 08:39:10.453646+00	1	\N	\N	f	f
2302	COST_CENTER	Cost Center	Bella Technologies	9883	2022-09-20 08:39:10.453703+00	2022-09-20 08:39:10.453731+00	1	\N	\N	f	f
2303	COST_CENTER	Cost Center	Bell Canada	9884	2022-09-20 08:39:10.453788+00	2022-09-20 08:39:10.453815+00	1	\N	\N	f	f
2304	COST_CENTER	Cost Center	Benthic Petroleum	9885	2022-09-20 08:39:10.453872+00	2022-09-20 08:39:10.453899+00	1	\N	\N	f	f
2305	COST_CENTER	Cost Center	Biffco	9886	2022-09-20 08:39:10.453956+00	2022-09-20 08:39:10.453983+00	1	\N	\N	f	f
2306	COST_CENTER	Cost Center	Big Blue Bubble	9887	2022-09-20 08:39:10.45404+00	2022-09-20 08:39:10.454067+00	1	\N	\N	f	f
2307	COST_CENTER	Cost Center	Billabong	9888	2022-09-20 08:39:10.454137+00	2022-09-20 08:39:10.454319+00	1	\N	\N	f	f
2308	COST_CENTER	Cost Center	Binford	9889	2022-09-20 08:39:10.45452+00	2022-09-20 08:39:10.454549+00	1	\N	\N	f	f
2309	COST_CENTER	Cost Center	Bing Lee	9890	2022-09-20 08:39:10.454746+00	2022-09-20 08:39:10.454775+00	1	\N	\N	f	f
2310	COST_CENTER	Cost Center	BioClear	9891	2022-09-20 08:39:10.455026+00	2022-09-20 08:39:10.45514+00	1	\N	\N	f	f
2311	COST_CENTER	Cost Center	BioMed Labs	9892	2022-09-20 08:39:10.455214+00	2022-09-20 08:39:10.455342+00	1	\N	\N	f	f
2312	COST_CENTER	Cost Center	Biovail	9893	2022-09-20 08:39:10.455449+00	2022-09-20 08:39:10.455477+00	1	\N	\N	f	f
2313	COST_CENTER	Cost Center	BlackBerry Limited	9894	2022-09-20 08:39:10.455534+00	2022-09-20 08:39:10.455561+00	1	\N	\N	f	f
2314	COST_CENTER	Cost Center	Black Hen Music	9895	2022-09-20 08:39:10.455631+00	2022-09-20 08:39:10.45566+00	1	\N	\N	f	f
2315	COST_CENTER	Cost Center	Bledsoe Cathcart Diestel and Pedersen LLP	9896	2022-09-20 08:39:10.455719+00	2022-09-20 08:39:10.455741+00	1	\N	\N	f	f
2316	COST_CENTER	Cost Center	Blenz Coffee	9897	2022-09-20 08:39:10.456019+00	2022-09-20 08:39:10.45605+00	1	\N	\N	f	f
2317	COST_CENTER	Cost Center	BlogXS	9898	2022-09-20 08:39:10.456112+00	2022-09-20 08:39:10.456142+00	1	\N	\N	f	f
2318	COST_CENTER	Cost Center	Bluejam	9899	2022-09-20 08:39:10.456196+00	2022-09-20 08:39:10.456215+00	1	\N	\N	f	f
2319	COST_CENTER	Cost Center	BlueScope	9900	2022-09-20 08:39:10.456399+00	2022-09-20 08:39:10.456431+00	1	\N	\N	f	f
2320	COST_CENTER	Cost Center	Blue Sun Corporation	9901	2022-09-20 08:39:10.456493+00	2022-09-20 08:39:10.456518+00	1	\N	\N	f	f
2321	COST_CENTER	Cost Center	Blundstone Footwear	9902	2022-09-20 08:39:10.456565+00	2022-09-20 08:39:10.456576+00	1	\N	\N	f	f
2322	COST_CENTER	Cost Center	Bluth Company	9903	2022-09-20 08:39:10.456626+00	2022-09-20 08:39:10.456655+00	1	\N	\N	f	f
2323	COST_CENTER	Cost Center	Boeing Canada	9904	2022-09-20 08:39:10.456715+00	2022-09-20 08:39:10.456764+00	1	\N	\N	f	f
2324	COST_CENTER	Cost Center	Boost Juice Bars	9905	2022-09-20 08:39:10.462992+00	2022-09-20 08:39:10.463039+00	1	\N	\N	f	f
2325	COST_CENTER	Cost Center	Boral	9906	2022-09-20 08:39:10.463125+00	2022-09-20 08:39:10.463154+00	1	\N	\N	f	f
2326	COST_CENTER	Cost Center	Boston Pizza	9907	2022-09-20 08:39:10.463245+00	2022-09-20 08:39:10.463423+00	1	\N	\N	f	f
2327	COST_CENTER	Cost Center	Bottle Rocket Apps	9908	2022-09-20 08:39:10.463539+00	2022-09-20 08:39:10.463569+00	1	\N	\N	f	f
2328	COST_CENTER	Cost Center	Bowring Brothers	9909	2022-09-20 08:39:10.463632+00	2022-09-20 08:39:10.463661+00	1	\N	\N	f	f
2329	COST_CENTER	Cost Center	Brainlounge	9910	2022-09-20 08:39:10.463722+00	2022-09-20 08:39:10.463751+00	1	\N	\N	f	f
2330	COST_CENTER	Cost Center	Brant, Agron, Meiselman	9911	2022-09-20 08:39:10.463812+00	2022-09-20 08:39:10.463983+00	1	\N	\N	f	f
2331	COST_CENTER	Cost Center	BrightSide Technologies	9912	2022-09-20 08:39:10.464152+00	2022-09-20 08:39:10.464181+00	1	\N	\N	f	f
2332	COST_CENTER	Cost Center	Brown Brothers Milawa Vineyard	9913	2022-09-20 08:39:10.464394+00	2022-09-20 08:39:10.464558+00	1	\N	\N	f	f
2333	COST_CENTER	Cost Center	Browsebug	9914	2022-09-20 08:39:10.464787+00	2022-09-20 08:39:10.464809+00	1	\N	\N	f	f
2334	COST_CENTER	Cost Center	Bruce Power	9915	2022-09-20 08:39:10.46501+00	2022-09-20 08:39:10.465131+00	1	\N	\N	f	f
2335	COST_CENTER	Cost Center	Bubblebox	9916	2022-09-20 08:39:10.465354+00	2022-09-20 08:39:10.465381+00	1	\N	\N	f	f
2336	COST_CENTER	Cost Center	Bubblemix	9917	2022-09-20 08:39:10.465438+00	2022-09-20 08:39:10.465465+00	1	\N	\N	f	f
2337	COST_CENTER	Cost Center	BuddyTV	9918	2022-09-20 08:39:10.465522+00	2022-09-20 08:39:10.465549+00	1	\N	\N	f	f
2338	COST_CENTER	Cost Center	Bulla Dairy Foods	9919	2022-09-20 08:39:10.465606+00	2022-09-20 08:39:10.465633+00	1	\N	\N	f	f
2339	COST_CENTER	Cost Center	Bullfrog Power	9920	2022-09-20 08:39:10.465689+00	2022-09-20 08:39:10.465716+00	1	\N	\N	f	f
2340	COST_CENTER	Cost Center	Burns Philp	9921	2022-09-20 08:39:10.465773+00	2022-09-20 08:39:10.4658+00	1	\N	\N	f	f
2341	COST_CENTER	Cost Center	Business Connexion Group	9922	2022-09-20 08:39:10.465857+00	2022-09-20 08:39:10.465884+00	1	\N	\N	f	f
2342	COST_CENTER	Cost Center	Buynlarge Corporation	9923	2022-09-20 08:39:10.46594+00	2022-09-20 08:39:10.465967+00	1	\N	\N	f	f
2343	COST_CENTER	Cost Center	Cadillac Fairview	9924	2022-09-20 08:39:10.466038+00	2022-09-20 08:39:10.466066+00	1	\N	\N	f	f
2344	COST_CENTER	Cost Center	Camperdown Dairy International	9925	2022-09-20 08:39:10.466122+00	2022-09-20 08:39:10.466149+00	1	\N	\N	f	f
2345	COST_CENTER	Cost Center	Canada Deposit Insurance Corporation	9926	2022-09-20 08:39:10.466205+00	2022-09-20 08:39:10.466233+00	1	\N	\N	f	f
2346	COST_CENTER	Cost Center	Canadian Bank Note Company	9927	2022-09-20 08:39:10.466289+00	2022-09-20 08:39:10.466316+00	1	\N	\N	f	f
2347	COST_CENTER	Cost Center	Canadian Light Source	9928	2022-09-20 08:39:10.466585+00	2022-09-20 08:39:10.466644+00	1	\N	\N	f	f
2348	COST_CENTER	Cost Center	Canadian Natural Resources	9929	2022-09-20 08:39:10.466748+00	2022-09-20 08:39:10.466785+00	1	\N	\N	f	f
2349	COST_CENTER	Cost Center	Canadian Steamship Lines	9930	2022-09-20 08:39:10.466862+00	2022-09-20 08:39:10.466892+00	1	\N	\N	f	f
2350	COST_CENTER	Cost Center	Canadian Tire Bank	9931	2022-09-20 08:39:10.466955+00	2022-09-20 08:39:10.466984+00	1	\N	\N	f	f
2351	COST_CENTER	Cost Center	Candente Copper	9932	2022-09-20 08:39:10.467047+00	2022-09-20 08:39:10.467171+00	1	\N	\N	f	f
2352	COST_CENTER	Cost Center	Candor Corp	9933	2022-09-20 08:39:10.467383+00	2022-09-20 08:39:10.467412+00	1	\N	\N	f	f
2353	COST_CENTER	Cost Center	CanJet	9934	2022-09-20 08:39:10.46747+00	2022-09-20 08:39:10.467498+00	1	\N	\N	f	f
2354	COST_CENTER	Cost Center	Capcom Vancouver	9935	2022-09-20 08:39:10.467554+00	2022-09-20 08:39:10.467581+00	1	\N	\N	f	f
2355	COST_CENTER	Cost Center	Capitec Bank	9936	2022-09-20 08:39:10.467637+00	2022-09-20 08:39:10.467664+00	1	\N	\N	f	f
2356	COST_CENTER	Cost Center	Capsule	9937	2022-09-20 08:39:10.467721+00	2022-09-20 08:39:10.467748+00	1	\N	\N	f	f
2357	COST_CENTER	Cost Center	Cardiovascular Disease Special	9938	2022-09-20 08:39:10.467823+00	2022-09-20 08:39:10.468126+00	1	\N	\N	f	f
2358	COST_CENTER	Cost Center	Carolina Health Centers, Inc.	9939	2022-09-20 08:39:10.468193+00	2022-09-20 08:39:10.468336+00	1	\N	\N	f	f
2359	COST_CENTER	Cost Center	Casavant Frares	9940	2022-09-20 08:39:10.46851+00	2022-09-20 08:39:10.46854+00	1	\N	\N	f	f
2360	COST_CENTER	Cost Center	Cathedral Software	9941	2022-09-20 08:39:10.468735+00	2022-09-20 08:39:10.468761+00	1	\N	\N	f	f
2361	COST_CENTER	Cost Center	CBH Group	9942	2022-09-20 08:39:10.468829+00	2022-09-20 08:39:10.468857+00	1	\N	\N	f	f
2362	COST_CENTER	Cost Center	Cbus	9943	2022-09-20 08:39:10.468913+00	2022-09-20 08:39:10.46894+00	1	\N	\N	f	f
2363	COST_CENTER	Cost Center	CDC Ixis North America Inc.	9944	2022-09-20 08:39:10.469145+00	2022-09-20 08:39:10.469173+00	1	\N	\N	f	f
2364	COST_CENTER	Cost Center	Cell C	9945	2022-09-20 08:39:10.46935+00	2022-09-20 08:39:10.46939+00	1	\N	\N	f	f
2365	COST_CENTER	Cost Center	Cellcom Communications	9946	2022-09-20 08:39:10.469447+00	2022-09-20 08:39:10.469474+00	1	\N	\N	f	f
2366	COST_CENTER	Cost Center	Centra Gas Manitoba Inc.	9947	2022-09-20 08:39:10.46953+00	2022-09-20 08:39:10.469557+00	1	\N	\N	f	f
2367	COST_CENTER	Cost Center	CGH Medical Center	9948	2022-09-20 08:39:10.469613+00	2022-09-20 08:39:10.46964+00	1	\N	\N	f	f
2368	COST_CENTER	Cost Center	Chapters	9949	2022-09-20 08:39:10.469696+00	2022-09-20 08:39:10.469723+00	1	\N	\N	f	f
2369	COST_CENTER	Cost Center	Checkers	9950	2022-09-20 08:39:10.469779+00	2022-09-20 08:39:10.469806+00	1	\N	\N	f	f
2370	COST_CENTER	Cost Center	CHEP	9951	2022-09-20 08:39:10.469863+00	2022-09-20 08:39:10.46989+00	1	\N	\N	f	f
2371	COST_CENTER	Cost Center	Chevron Texaco	9952	2022-09-20 08:39:10.469946+00	2022-09-20 08:39:10.469973+00	1	\N	\N	f	f
2372	COST_CENTER	Cost Center	CHOAM	9953	2022-09-20 08:39:10.47003+00	2022-09-20 08:39:10.470057+00	1	\N	\N	f	f
2373	COST_CENTER	Cost Center	Choices Market	9954	2022-09-20 08:39:10.470113+00	2022-09-20 08:39:10.47014+00	1	\N	\N	f	f
2374	COST_CENTER	Cost Center	CIMIC Group	9955	2022-09-20 08:39:10.482026+00	2022-09-20 08:39:10.482106+00	1	\N	\N	f	f
2375	COST_CENTER	Cost Center	Cinium Financial Services	9956	2022-09-20 08:39:10.483204+00	2022-09-20 08:39:10.483268+00	1	\N	\N	f	f
2376	COST_CENTER	Cost Center	Cirque du Soleil	9957	2022-09-20 08:39:10.483358+00	2022-09-20 08:39:10.483393+00	1	\N	\N	f	f
2377	COST_CENTER	Cost Center	Citizens Communications	9958	2022-09-20 08:39:10.48364+00	2022-09-20 08:39:10.483679+00	1	\N	\N	f	f
2378	COST_CENTER	Cost Center	Cleco Corporation	9959	2022-09-20 08:39:10.483753+00	2022-09-20 08:39:10.483784+00	1	\N	\N	f	f
2379	COST_CENTER	Cost Center	Clerby	9960	2022-09-20 08:39:10.483854+00	2022-09-20 08:39:10.483884+00	1	\N	\N	f	f
2380	COST_CENTER	Cost Center	CMV Group	9961	2022-09-20 08:39:10.483949+00	2022-09-20 08:39:10.483979+00	1	\N	\N	f	f
2381	COST_CENTER	Cost Center	Coachman Insurance Company	9962	2022-09-20 08:39:10.484042+00	2022-09-20 08:39:10.484072+00	1	\N	\N	f	f
2382	COST_CENTER	Cost Center	Coca-Cola Amatil	9963	2022-09-20 08:39:10.484135+00	2022-09-20 08:39:10.484498+00	1	\N	\N	f	f
2383	COST_CENTER	Cost Center	Coles Group	9964	2022-09-20 08:39:10.484704+00	2022-09-20 08:39:10.484745+00	1	\N	\N	f	f
2384	COST_CENTER	Cost Center	Column Five	9965	2022-09-20 08:39:10.48482+00	2022-09-20 08:39:10.484857+00	1	\N	\N	f	f
2385	COST_CENTER	Cost Center	Comm100	9966	2022-09-20 08:39:10.484934+00	2022-09-20 08:39:10.484966+00	1	\N	\N	f	f
2386	COST_CENTER	Cost Center	Commonwealth Bank	9967	2022-09-20 08:39:10.48506+00	2022-09-20 08:39:10.48509+00	1	\N	\N	f	f
2387	COST_CENTER	Cost Center	Community Agency Services	9968	2022-09-20 08:39:10.485168+00	2022-09-20 08:39:10.485201+00	1	\N	\N	f	f
2388	COST_CENTER	Cost Center	Compass Investment Partners	9969	2022-09-20 08:39:10.48541+00	2022-09-20 08:39:10.485513+00	1	\N	\N	f	f
2389	COST_CENTER	Cost Center	Compass Resources	9970	2022-09-20 08:39:10.485635+00	2022-09-20 08:39:10.485676+00	1	\N	\N	f	f
2390	COST_CENTER	Cost Center	Computer Sciences Corporation	9971	2022-09-20 08:39:10.485755+00	2022-09-20 08:39:10.485784+00	1	\N	\N	f	f
2391	COST_CENTER	Cost Center	Computershare	9972	2022-09-20 08:39:10.485846+00	2022-09-20 08:39:10.485876+00	1	\N	\N	f	f
2392	COST_CENTER	Cost Center	ComTron	9973	2022-09-20 08:39:10.485937+00	2022-09-20 08:39:10.485966+00	1	\N	\N	f	f
2393	COST_CENTER	Cost Center	Conductor	9974	2022-09-20 08:39:10.486027+00	2022-09-20 08:39:10.486056+00	1	\N	\N	f	f
2394	COST_CENTER	Cost Center	Conestoga-Rovers and Associates	9975	2022-09-20 08:39:10.486141+00	2022-09-20 08:39:10.486182+00	1	\N	\N	f	f
2395	COST_CENTER	Cost Center	Conglomerated Amalgamated	9976	2022-09-20 08:39:10.4866+00	2022-09-20 08:39:10.486633+00	1	\N	\N	f	f
2396	COST_CENTER	Cost Center	Copper Ab	9977	2022-09-20 08:39:10.486702+00	2022-09-20 08:39:10.486745+00	1	\N	\N	f	f
2397	COST_CENTER	Cost Center	Cordiant Capital Inc.	9978	2022-09-20 08:39:10.486868+00	2022-09-20 08:39:10.486929+00	1	\N	\N	f	f
2398	COST_CENTER	Cost Center	Corley Energy	9979	2022-09-20 08:39:10.487038+00	2022-09-20 08:39:10.487079+00	1	\N	\N	f	f
2399	COST_CENTER	Cost Center	Corus Entertainment	9980	2022-09-20 08:39:10.487477+00	2022-09-20 08:39:10.487531+00	1	\N	\N	f	f
2400	COST_CENTER	Cost Center	CostLess Insurance	9981	2022-09-20 08:39:10.487614+00	2022-09-20 08:39:10.487647+00	1	\N	\N	f	f
2401	COST_CENTER	Cost Center	Cotton On	9982	2022-09-20 08:39:10.487716+00	2022-09-20 08:39:10.48778+00	1	\N	\N	f	f
2402	COST_CENTER	Cost Center	Country Energy	9983	2022-09-20 08:39:10.488089+00	2022-09-20 08:39:10.488126+00	1	\N	\N	f	f
2403	COST_CENTER	Cost Center	Country Style	9984	2022-09-20 08:39:10.488599+00	2022-09-20 08:39:10.488654+00	1	\N	\N	f	f
2404	COST_CENTER	Cost Center	Creative Healthcare	9985	2022-09-20 08:39:10.489024+00	2022-09-20 08:39:10.489077+00	1	\N	\N	f	f
2405	COST_CENTER	Cost Center	Crestline Coach	9986	2022-09-20 08:39:10.489147+00	2022-09-20 08:39:10.489175+00	1	\N	\N	f	f
2406	COST_CENTER	Cost Center	Crossecom	9987	2022-09-20 08:39:10.489235+00	2022-09-20 08:39:10.489263+00	1	\N	\N	f	f
2407	COST_CENTER	Cost Center	Crown Resorts	9988	2022-09-20 08:39:10.489321+00	2022-09-20 08:39:10.48936+00	1	\N	\N	f	f
2408	COST_CENTER	Cost Center	CSL Limited	9989	2022-09-20 08:39:10.489642+00	2022-09-20 08:39:10.489665+00	1	\N	\N	f	f
2409	COST_CENTER	Cost Center	CSR Limited	9990	2022-09-20 08:39:10.489718+00	2022-09-20 08:39:10.489746+00	1	\N	\N	f	f
2410	COST_CENTER	Cost Center	CTV Television Network	9991	2022-09-20 08:39:10.489801+00	2022-09-20 08:39:10.489831+00	1	\N	\N	f	f
2411	COST_CENTER	Cost Center	Cuna Mutual Insurance Society	9992	2022-09-20 08:39:10.489892+00	2022-09-20 08:39:10.489922+00	1	\N	\N	f	f
2412	COST_CENTER	Cost Center	Cvibe Insurance	9993	2022-09-20 08:39:10.489982+00	2022-09-20 08:39:10.490011+00	1	\N	\N	f	f
2413	COST_CENTER	Cost Center	Cyberdyne Systems	9994	2022-09-20 08:39:10.490072+00	2022-09-20 08:39:10.490101+00	1	\N	\N	f	f
2414	COST_CENTER	Cost Center	Cymax Stores	9995	2022-09-20 08:39:10.490161+00	2022-09-20 08:39:10.49019+00	1	\N	\N	f	f
2415	COST_CENTER	Cost Center	Cymer	9996	2022-09-20 08:39:10.49025+00	2022-09-20 08:39:10.490279+00	1	\N	\N	f	f
2416	COST_CENTER	Cost Center	Cym Labs	9997	2022-09-20 08:39:10.490344+00	2022-09-20 08:39:10.490462+00	1	\N	\N	f	f
2417	COST_CENTER	Cost Center	Dabtype	9998	2022-09-20 08:39:10.490534+00	2022-09-20 08:39:10.490562+00	1	\N	\N	f	f
2418	COST_CENTER	Cost Center	Dabvine	9999	2022-09-20 08:39:10.490618+00	2022-09-20 08:39:10.490645+00	1	\N	\N	f	f
2419	COST_CENTER	Cost Center	Dare Foods	10000	2022-09-20 08:39:10.490701+00	2022-09-20 08:39:10.490732+00	1	\N	\N	f	f
2420	COST_CENTER	Cost Center	DataDyne	10001	2022-09-20 08:39:10.49079+00	2022-09-20 08:39:10.490817+00	1	\N	\N	f	f
2421	COST_CENTER	Cost Center	David Jones Limited	10002	2022-09-20 08:39:10.490874+00	2022-09-20 08:39:10.490901+00	1	\N	\N	f	f
2422	COST_CENTER	Cost Center	Davis and Young LPA	10003	2022-09-20 08:39:10.490958+00	2022-09-20 08:39:10.490985+00	1	\N	\N	f	f
2423	COST_CENTER	Cost Center	Adidas	9584	2022-09-20 08:39:10.491041+00	2022-09-20 08:39:10.491068+00	1	\N	\N	f	f
2424	COST_CENTER	Cost Center	Fabrication	9585	2022-09-20 08:39:10.497515+00	2022-09-20 08:39:10.497607+00	1	\N	\N	f	f
2425	COST_CENTER	Cost Center	FAE	9586	2022-09-20 08:39:10.498314+00	2022-09-20 08:39:10.499646+00	1	\N	\N	f	f
2426	COST_CENTER	Cost Center	Eastside	9536	2022-09-20 08:39:10.500517+00	2022-09-20 08:39:10.500653+00	1	\N	\N	f	f
2427	COST_CENTER	Cost Center	North	9537	2022-09-20 08:39:10.50096+00	2022-09-20 08:39:10.501164+00	1	\N	\N	f	f
2428	COST_CENTER	Cost Center	South	9538	2022-09-20 08:39:10.502041+00	2022-09-20 08:39:10.502182+00	1	\N	\N	f	f
2429	COST_CENTER	Cost Center	West Coast	9539	2022-09-20 08:39:10.502482+00	2022-09-20 08:39:10.502517+00	1	\N	\N	f	f
2430	COST_CENTER	Cost Center	Legal and Secretarial	7229	2022-09-20 08:39:10.502586+00	2022-09-20 08:39:10.502613+00	1	\N	\N	f	f
2431	COST_CENTER	Cost Center	Strategy Planning	7228	2022-09-20 08:39:10.50267+00	2022-09-20 08:39:10.502698+00	1	\N	\N	f	f
2432	COST_CENTER	Cost Center	Administration	7227	2022-09-20 08:39:10.502754+00	2022-09-20 08:39:10.502781+00	1	\N	\N	f	f
2433	COST_CENTER	Cost Center	Retail	7226	2022-09-20 08:39:10.502838+00	2022-09-20 08:39:10.502865+00	1	\N	\N	f	f
2434	COST_CENTER	Cost Center	SME	7225	2022-09-20 08:39:10.502921+00	2022-09-20 08:39:10.502948+00	1	\N	\N	f	f
2435	COST_CENTER	Cost Center	Marketing	7224	2022-09-20 08:39:10.503004+00	2022-09-20 08:39:10.503032+00	1	\N	\N	f	f
2436	COST_CENTER	Cost Center	Audit	7223	2022-09-20 08:39:10.503088+00	2022-09-20 08:39:10.503115+00	1	\N	\N	f	f
2437	COST_CENTER	Cost Center	Treasury	7222	2022-09-20 08:39:10.503171+00	2022-09-20 08:39:10.503199+00	1	\N	\N	f	f
2438	COST_CENTER	Cost Center	Internal	7221	2022-09-20 08:39:10.503255+00	2022-09-20 08:39:10.503282+00	1	\N	\N	f	f
2439	COST_CENTER	Cost Center	Sales and Cross	7220	2022-09-20 08:39:10.503338+00	2022-09-20 08:39:10.503367+00	1	\N	\N	f	f
3180	MERCHANT	Merchant	Entity V700	852	2022-09-20 08:40:24.029423+00	2022-09-20 08:40:24.02945+00	1	\N	\N	f	f
683	PROJECT	Project	Project 7	203315	2022-09-20 08:39:06.850486+00	2022-09-20 08:39:06.850626+00	1	t	\N	f	f
2712	TAX_GROUP	Tax Group	71DTN3JPS4	tg3s7XQ9gMS8	2022-09-20 08:39:11.576836+00	2022-09-20 08:39:11.576896+00	1	\N	{"tax_rate": 0.18}	f	f
3043	MERCHANT	Merchant	Ashwin	852	2022-09-20 08:40:15.786052+00	2022-09-20 08:40:15.78614+00	1	\N	\N	f	f
3079	MERCHANT	Merchant	Samantha Washington	852	2022-09-20 08:40:15.889336+00	2022-09-20 08:40:15.889366+00	1	\N	\N	f	f
2745	TAX_GROUP	Tax Group	ITS-AU @0.0%	tg9e1bqo5zgV	2022-09-20 08:39:11.626516+00	2022-09-20 08:39:11.626589+00	1	\N	{"tax_rate": 0.0}	f	f
3085	MERCHANT	Merchant	test Sharma	852	2022-09-20 08:40:15.929612+00	2022-09-20 08:40:15.929654+00	1	\N	\N	f	f
3098	MERCHANT	Merchant	Ashwin from NetSuite	852	2022-09-20 08:40:15.969892+00	2022-09-20 08:40:15.969921+00	1	\N	\N	f	f
2746	TAX_GROUP	Tax Group	2VD4DE3305	tg9KXJlbl0fo	2022-09-20 08:39:11.626755+00	2022-09-20 08:39:11.62773+00	1	\N	{"tax_rate": 0.18}	f	f
2547	LOCATION_ENTITY	Location Entity	Wedding Planning by Whitney	expense_custom_field.location entity.1	2022-09-20 08:39:10.945031+00	2022-09-20 08:39:10.945075+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2548	LOCATION_ENTITY	Location Entity	Jeff's Jalopies	expense_custom_field.location entity.2	2022-09-20 08:39:10.945155+00	2022-09-20 08:39:10.945185+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2549	LOCATION_ENTITY	Location Entity	Dylan Sollfrank	expense_custom_field.location entity.3	2022-09-20 08:39:10.945253+00	2022-09-20 08:39:10.945281+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2550	LOCATION_ENTITY	Location Entity	Diego Rodriguez	expense_custom_field.location entity.4	2022-09-20 08:39:10.945349+00	2022-09-20 08:39:10.945376+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2551	LOCATION_ENTITY	Location Entity	Ashwinn	expense_custom_field.location entity.5	2022-09-20 08:39:10.945645+00	2022-09-20 08:39:10.945682+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2552	LOCATION_ENTITY	Location Entity	Geeta Kalapatapu	expense_custom_field.location entity.6	2022-09-20 08:39:10.94576+00	2022-09-20 08:39:10.945788+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2553	LOCATION_ENTITY	Location Entity	Travis Waldron	expense_custom_field.location entity.7	2022-09-20 08:39:10.945854+00	2022-09-20 08:39:10.945881+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2554	LOCATION_ENTITY	Location Entity	USA3	expense_custom_field.location entity.8	2022-09-20 08:39:10.945945+00	2022-09-20 08:39:10.945972+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
684	PROJECT	Project	Project 8	203316	2022-09-20 08:39:06.867492+00	2022-09-20 08:39:06.867576+00	1	t	\N	f	f
2555	LOCATION_ENTITY	Location Entity	Dukes Basketball Camp	expense_custom_field.location entity.9	2022-09-20 08:39:10.946037+00	2022-09-20 08:39:10.946064+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2677	CORPORATE_CARD	Corporate Card	BANK OF INDIA - 219876	baccfiqYgkE8Db	2022-09-20 08:39:11.191992+00	2022-09-20 08:39:11.19202+00	1	\N	{"cardholder_name": null}	f	f
2556	LOCATION_ENTITY	Location Entity	Weiskopf Consulting	expense_custom_field.location entity.10	2022-09-20 08:39:10.946128+00	2022-09-20 08:39:10.946156+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2557	LOCATION_ENTITY	Location Entity	Mark Cho	expense_custom_field.location entity.11	2022-09-20 08:39:10.94622+00	2022-09-20 08:39:10.946247+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2558	LOCATION_ENTITY	Location Entity	Diego Rodriguez:Test Project	expense_custom_field.location entity.12	2022-09-20 08:39:10.946311+00	2022-09-20 08:39:10.946476+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2559	LOCATION_ENTITY	Location Entity	India	expense_custom_field.location entity.13	2022-09-20 08:39:10.946554+00	2022-09-20 08:39:10.946582+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2560	LOCATION_ENTITY	Location Entity	Pye's Cakes	expense_custom_field.location entity.14	2022-09-20 08:39:10.946646+00	2022-09-20 08:39:10.946673+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2561	LOCATION_ENTITY	Location Entity	Freeman Sporting Goods:55 Twin Lane	expense_custom_field.location entity.15	2022-09-20 08:39:10.94677+00	2022-09-20 08:39:10.946799+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2562	LOCATION_ENTITY	Location Entity	Shara Barnett:Barnett Design	expense_custom_field.location entity.16	2022-09-20 08:39:10.946868+00	2022-09-20 08:39:10.946897+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2563	LOCATION_ENTITY	Location Entity	Amy's Bird Sanctuary	expense_custom_field.location entity.17	2022-09-20 08:39:10.946965+00	2022-09-20 08:39:10.946994+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2564	LOCATION_ENTITY	Location Entity	Amy's Bird Sanctuary:Test Project	expense_custom_field.location entity.18	2022-09-20 08:39:10.947063+00	2022-09-20 08:39:10.947091+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2565	LOCATION_ENTITY	Location Entity	Gevelber Photography	expense_custom_field.location entity.19	2022-09-20 08:39:10.947165+00	2022-09-20 08:39:10.947195+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2566	LOCATION_ENTITY	Location Entity	Red Rock Diner	expense_custom_field.location entity.20	2022-09-20 08:39:10.947265+00	2022-09-20 08:39:10.947295+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2567	LOCATION_ENTITY	Location Entity	Cool Cars	expense_custom_field.location entity.21	2022-09-20 08:39:10.947513+00	2022-09-20 08:39:10.947546+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2568	LOCATION_ENTITY	Location Entity	Rago Travel Agency	expense_custom_field.location entity.22	2022-09-20 08:39:10.947625+00	2022-09-20 08:39:10.947652+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2569	LOCATION_ENTITY	Location Entity	Sravan BLR Customer	expense_custom_field.location entity.23	2022-09-20 08:39:10.947717+00	2022-09-20 08:39:10.947745+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2570	LOCATION_ENTITY	Location Entity	John Melton	expense_custom_field.location entity.24	2022-09-20 08:39:10.947809+00	2022-09-20 08:39:10.947836+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2571	LOCATION_ENTITY	Location Entity	USA1	expense_custom_field.location entity.25	2022-09-20 08:39:10.947901+00	2022-09-20 08:39:10.947928+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2572	LOCATION_ENTITY	Location Entity	Bill's Windsurf Shop	expense_custom_field.location entity.26	2022-09-20 08:39:10.947992+00	2022-09-20 08:39:10.94802+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2573	LOCATION_ENTITY	Location Entity	Paulsen Medical Supplies	expense_custom_field.location entity.27	2022-09-20 08:39:10.948084+00	2022-09-20 08:39:10.948111+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2574	LOCATION_ENTITY	Location Entity	Freeman Sporting Goods:0969 Ocean View Road	expense_custom_field.location entity.28	2022-09-20 08:39:10.948176+00	2022-09-20 08:39:10.948203+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2575	LOCATION_ENTITY	Location Entity	Kate Whelan	expense_custom_field.location entity.29	2022-09-20 08:39:10.948268+00	2022-09-20 08:39:10.948295+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2576	LOCATION_ENTITY	Location Entity	Freeman Sporting Goods	expense_custom_field.location entity.30	2022-09-20 08:39:10.948373+00	2022-09-20 08:39:10.948536+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2577	LOCATION_ENTITY	Location Entity	Shara Barnett	expense_custom_field.location entity.31	2022-09-20 08:39:10.948648+00	2022-09-20 08:39:10.948667+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
3100	MERCHANT	Merchant	Blob Johnson	852	2022-09-20 08:40:15.970071+00	2022-09-20 08:40:15.970199+00	1	\N	\N	f	f
2578	LOCATION_ENTITY	Location Entity	Rondonuwu Fruit and Vegi	expense_custom_field.location entity.32	2022-09-20 08:39:10.948717+00	2022-09-20 08:39:10.948739+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2579	LOCATION_ENTITY	Location Entity	Video Games by Dan	expense_custom_field.location entity.33	2022-09-20 08:39:10.948808+00	2022-09-20 08:39:10.948838+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2580	LOCATION_ENTITY	Location Entity	Sushi by Katsuyuki	expense_custom_field.location entity.34	2022-09-20 08:39:10.948902+00	2022-09-20 08:39:10.948913+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2581	LOCATION_ENTITY	Location Entity	USA2	expense_custom_field.location entity.35	2022-09-20 08:39:10.948964+00	2022-09-20 08:39:10.948981+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2582	LOCATION_ENTITY	Location Entity	Kookies by Kathy	expense_custom_field.location entity.36	2022-09-20 08:39:10.949035+00	2022-09-20 08:39:10.949059+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
2583	LOCATION_ENTITY	Location Entity	Sonnenschein Family Store	expense_custom_field.location entity.37	2022-09-20 08:39:10.949119+00	2022-09-20 08:39:10.949141+00	1	\N	{"placeholder": "Select Location Entity", "custom_field_id": 179638}	f	f
3086	MERCHANT	Merchant	Tim Philip Masonry	852	2022-09-20 08:40:15.929809+00	2022-09-20 08:40:15.929843+00	1	\N	\N	f	f
3099	MERCHANT	Merchant	Basket Case	852	2022-09-20 08:40:15.969982+00	2022-09-20 08:40:15.970011+00	1	\N	\N	f	f
3101	MERCHANT	Merchant	Blooper Bloop	852	2022-09-20 08:40:15.970263+00	2022-09-20 08:40:15.970292+00	1	\N	\N	f	f
2699	TAX_GROUP	Tax Group	CA-Zero @0.0%	tg1KNSwtyeAW	2022-09-20 08:39:11.572056+00	2022-09-20 08:39:11.572106+00	1	\N	{"tax_rate": 0.0}	f	f
2713	TAX_GROUP	Tax Group	V1EJ6D8VGJ	tg45EVaI4yoO	2022-09-20 08:39:11.577033+00	2022-09-20 08:39:11.577082+00	1	\N	{"tax_rate": 0.18}	f	f
2688	CORPORATE_CARD	Corporate Card	American Express - 29578	bacce3rbqv5Veb	2022-09-20 08:39:11.194168+00	2022-09-20 08:39:11.194195+00	1	\N	{"cardholder_name": "Monica E. Geller-Bing's account"}	f	f
2674	CORPORATE_CARD	Corporate Card	BANK OF INDIA - 219875	baccKkmmW4u1N4	2022-09-20 08:39:11.191689+00	2022-09-20 08:39:11.19173+00	1	\N	{"cardholder_name": null}	f	f
2675	CORPORATE_CARD	Corporate Card	Bank of America - 1319	baccJKh39lWI2L	2022-09-20 08:39:11.191804+00	2022-09-20 08:39:11.191833+00	1	\N	{"cardholder_name": null}	f	f
2676	CORPORATE_CARD	Corporate Card	BANK OF INDIA - 219874	baccxoXQr0p2kj	2022-09-20 08:39:11.191899+00	2022-09-20 08:39:11.191927+00	1	\N	{"cardholder_name": null}	f	f
2678	CORPORATE_CARD	Corporate Card	American Express - 71149	baccaQY7KB7ogS	2022-09-20 08:39:11.192085+00	2022-09-20 08:39:11.192113+00	1	\N	{"cardholder_name": "Joseph Francis Tribbiani, Jr's account"}	f	f
2679	CORPORATE_CARD	Corporate Card	Bank of America - 8084	baccMCkKmsHV9X	2022-09-20 08:39:11.192178+00	2022-09-20 08:39:11.192205+00	1	\N	{"cardholder_name": null}	f	f
2731	TAX_GROUP	Tax Group	QZP8MCPJI0	tg7fDMpgFvdu	2022-09-20 08:39:11.591681+00	2022-09-20 08:39:11.591736+00	1	\N	{"tax_rate": 0.18}	f	f
2680	CORPORATE_CARD	Corporate Card	American Express - 30350	bacc3D6qx7cb4J	2022-09-20 08:39:11.19227+00	2022-09-20 08:39:11.192297+00	1	\N	{"cardholder_name": "Dr. Ross Eustace Geller's account"}	f	f
2681	CORPORATE_CARD	Corporate Card	American Express - 05556	baccuGmJMILiAr	2022-09-20 08:39:11.192703+00	2022-09-20 08:39:11.192787+00	1	\N	{"cardholder_name": "Phoebe Buffay-Hannigan's account"}	f	f
2682	CORPORATE_CARD	Corporate Card	American Express - 93634	bacc8nxvDzy9UB	2022-09-20 08:39:11.192881+00	2022-09-20 08:39:11.19291+00	1	\N	{"cardholder_name": "Joseph Francis Tribbiani, Jr's account"}	f	f
2683	CORPORATE_CARD	Corporate Card	American Express - 59344	baccRUz3T9WTG0	2022-09-20 08:39:11.19308+00	2022-09-20 08:39:11.193164+00	1	\N	{"cardholder_name": "Dr. Ross Eustace Geller's account"}	f	f
2684	CORPORATE_CARD	Corporate Card	American Express - 29676	baccJEu4LHANTj	2022-09-20 08:39:11.193557+00	2022-09-20 08:39:11.193607+00	1	\N	{"cardholder_name": "Monica E. Geller-Bing's account"}	f	f
2685	CORPORATE_CARD	Corporate Card	American Express - 97584	bacc3gPRo0BFI4	2022-09-20 08:39:11.193716+00	2022-09-20 08:39:11.193815+00	1	\N	{"cardholder_name": "Monica E. Geller-Bing's account"}	f	f
2686	CORPORATE_CARD	Corporate Card	American Express - 27881	baccT6Cr2LOoCU	2022-09-20 08:39:11.193978+00	2022-09-20 08:39:11.194008+00	1	\N	{"cardholder_name": "Monica E. Geller-Bing's account"}	f	f
2687	CORPORATE_CARD	Corporate Card	American Express - 40414	baccChwshlFsT5	2022-09-20 08:39:11.194076+00	2022-09-20 08:39:11.194104+00	1	\N	{"cardholder_name": "Monica E. Geller-Bing's account"}	f	f
2689	CORPORATE_CARD	Corporate Card	American Express - 93356	baccUhWPMgn4EB	2022-09-20 08:39:11.19426+00	2022-09-20 08:39:11.194288+00	1	\N	{"cardholder_name": "Dr. Ross Eustace Geller's account"}	f	f
2690	CORPORATE_CARD	Corporate Card	American Express - 64504	baccE0fU1LTqxm	2022-09-20 08:39:11.194353+00	2022-09-20 08:39:11.19439+00	1	\N	{"cardholder_name": "Joseph Francis Tribbiani, Jr's account"}	f	f
2691	CORPORATE_CARD	Corporate Card	American Express - 69115	baccKzSkYJjBQt	2022-09-20 08:39:11.194549+00	2022-09-20 08:39:11.194575+00	1	\N	{"cardholder_name": "Joseph Francis Tribbiani, Jr's account"}	f	f
2693	TAX_GROUP	Tax Group	LTFKCOG3FH	tg06xvLojY5h	2022-09-20 08:39:11.565609+00	2022-09-20 08:39:11.565649+00	1	\N	{"tax_rate": 0.18}	f	f
2694	TAX_GROUP	Tax Group	GST: NCF-AU @0.0%	tg09S3rMTTpo	2022-09-20 08:39:11.565774+00	2022-09-20 08:39:11.56581+00	1	\N	{"tax_rate": 0.0}	f	f
2695	TAX_GROUP	Tax Group	CGST	tg0fPRBFMZj7	2022-09-20 08:39:11.566245+00	2022-09-20 08:39:11.566304+00	1	\N	{"tax_rate": 0.5}	f	f
2696	TAX_GROUP	Tax Group	Z90LGUXCKD	tg0vUVJLRPvA	2022-09-20 08:39:11.566512+00	2022-09-20 08:39:11.567168+00	1	\N	{"tax_rate": 0.18}	f	f
2697	TAX_GROUP	Tax Group	R3BO0U5YZF	tg0vxs8Hz5F9	2022-09-20 08:39:11.567715+00	2022-09-20 08:39:11.567789+00	1	\N	{"tax_rate": 0.18}	f	f
2698	TAX_GROUP	Tax Group	PMNG0N8KSZ	tg1FdqJCybJs	2022-09-20 08:39:11.570109+00	2022-09-20 08:39:11.570194+00	1	\N	{"tax_rate": 0.18}	f	f
2700	TAX_GROUP	Tax Group	MTD7QH6N7D	tg1QK6lhb8J1	2022-09-20 08:39:11.572435+00	2022-09-20 08:39:11.572536+00	1	\N	{"tax_rate": 0.18}	f	f
2701	TAX_GROUP	Tax Group	QT8T97FF18	tg1Wr2J6mG2S	2022-09-20 08:39:11.572958+00	2022-09-20 08:39:11.573223+00	1	\N	{"tax_rate": 0.18}	f	f
2702	TAX_GROUP	Tax Group	RGLB5QES1M	tg1xpyImHPmA	2022-09-20 08:39:11.574082+00	2022-09-20 08:39:11.574216+00	1	\N	{"tax_rate": 0.18}	f	f
2703	TAX_GROUP	Tax Group	GV18OGZEWB	tg1ZsmGFRGSw	2022-09-20 08:39:11.574509+00	2022-09-20 08:39:11.574564+00	1	\N	{"tax_rate": 0.18}	f	f
2704	TAX_GROUP	Tax Group	WSTNCJ6Q5H	tg2bqtQzmNiO	2022-09-20 08:39:11.574976+00	2022-09-20 08:39:11.575011+00	1	\N	{"tax_rate": 0.18}	f	f
2705	TAX_GROUP	Tax Group	PST_CA_E @0.0%	tg2ecP3KC9Bk	2022-09-20 08:39:11.575101+00	2022-09-20 08:39:11.575133+00	1	\N	{"tax_rate": 0.0}	f	f
2706	TAX_GROUP	Tax Group	QVOZSLTNXZ	tg2lDhvY1epZ	2022-09-20 08:39:11.575583+00	2022-09-20 08:39:11.575921+00	1	\N	{"tax_rate": 0.18}	f	f
2707	TAX_GROUP	Tax Group	04DFQBACPE	tg30QAE0HLxw	2022-09-20 08:39:11.576059+00	2022-09-20 08:39:11.576105+00	1	\N	{"tax_rate": 0.18}	f	f
2708	TAX_GROUP	Tax Group	tax for xero @2.5%	tg38zIMqqDn3	2022-09-20 08:39:11.5763+00	2022-09-20 08:39:11.576323+00	1	\N	{"tax_rate": 0.03}	f	f
2709	TAX_GROUP	Tax Group	JHLK63ZZWB	tg3ArwZPL3it	2022-09-20 08:39:11.576398+00	2022-09-20 08:39:11.57649+00	1	\N	{"tax_rate": 0.18}	f	f
2710	TAX_GROUP	Tax Group	UK Tax @0.0%	tg3fLCqgcmCE	2022-09-20 08:39:11.576569+00	2022-09-20 08:39:11.576593+00	1	\N	{"tax_rate": 0.0}	f	f
2711	TAX_GROUP	Tax Group	VAT: UNDEF-GB @0.0%	tg3Luhktgf4N	2022-09-20 08:39:11.576672+00	2022-09-20 08:39:11.576701+00	1	\N	{"tax_rate": 0.0}	f	f
2714	TAX_GROUP	Tax Group	BNDNQCGL2A	tg49NLOzlAlX	2022-09-20 08:39:11.577202+00	2022-09-20 08:39:11.577244+00	1	\N	{"tax_rate": 0.18}	f	f
2715	TAX_GROUP	Tax Group	M20BG0G6TW	tg4MdV2zG6xY	2022-09-20 08:39:11.578266+00	2022-09-20 08:39:11.578334+00	1	\N	{"tax_rate": 0.18}	f	f
2716	TAX_GROUP	Tax Group	OEAN2S0661	tg4mhXQy2iSF	2022-09-20 08:39:11.579198+00	2022-09-20 08:39:11.579567+00	1	\N	{"tax_rate": 0.18}	f	f
2717	TAX_GROUP	Tax Group	XN7QJZBTGW	tg4UlWDpIpOz	2022-09-20 08:39:11.579801+00	2022-09-20 08:39:11.579961+00	1	\N	{"tax_rate": 0.18}	f	f
2718	TAX_GROUP	Tax Group	Tax on Goods @8.75%	tg4Zf3dJR6TA	2022-09-20 08:39:11.581067+00	2022-09-20 08:39:11.581192+00	1	\N	{"tax_rate": 0.09}	f	f
2719	TAX_GROUP	Tax Group	WWBU4JTK1W	tg4zTkLu4CGR	2022-09-20 08:39:11.582506+00	2022-09-20 08:39:11.582595+00	1	\N	{"tax_rate": 0.18}	f	f
2721	TAX_GROUP	Tax Group	HBKP7A0DNR	tg555KAYmC0B	2022-09-20 08:39:11.583118+00	2022-09-20 08:39:11.58317+00	1	\N	{"tax_rate": 0.18}	f	f
2722	TAX_GROUP	Tax Group	HOUPXN0V9X	tg5lJAlaYA8W	2022-09-20 08:39:11.583458+00	2022-09-20 08:39:11.583516+00	1	\N	{"tax_rate": 0.18}	f	f
2723	TAX_GROUP	Tax Group	EOHGT9QJO4	tg5MZxx4nAkU	2022-09-20 08:39:11.583643+00	2022-09-20 08:39:11.583686+00	1	\N	{"tax_rate": 0.18}	f	f
2724	TAX_GROUP	Tax Group	GST: TFS-AU @0.0%	tg5uf1kTpljU	2022-09-20 08:39:11.583804+00	2022-09-20 08:39:11.583845+00	1	\N	{"tax_rate": 0.0}	f	f
2726	TAX_GROUP	Tax Group	MB - GST/RST on Sales @12.0%	tg6rxcPps3Dd	2022-09-20 08:39:11.58412+00	2022-09-20 08:39:11.585432+00	1	\N	{"tax_rate": 0.12}	f	f
2727	TAX_GROUP	Tax Group	Out of scope @0%	tg6TnmXD9sUE	2022-09-20 08:39:11.586393+00	2022-09-20 08:39:11.586469+00	1	\N	{"tax_rate": 0.0}	f	f
2728	TAX_GROUP	Tax Group	62WRSSZKV3	tg6uJjoWWr5a	2022-09-20 08:39:11.586793+00	2022-09-20 08:39:11.586842+00	1	\N	{"tax_rate": 0.18}	f	f
2729	TAX_GROUP	Tax Group	8RJGQU3LBA	tg6VRu2QbZXW	2022-09-20 08:39:11.586963+00	2022-09-20 08:39:11.587003+00	1	\N	{"tax_rate": 0.18}	f	f
2730	TAX_GROUP	Tax Group	69W9JMEXIP	tg7AUo9qgugX	2022-09-20 08:39:11.587112+00	2022-09-20 08:39:11.587151+00	1	\N	{"tax_rate": 0.18}	f	f
2732	TAX_GROUP	Tax Group	M08GU5OX20	tg7IEw1ogNKf	2022-09-20 08:39:11.591841+00	2022-09-20 08:39:11.591875+00	1	\N	{"tax_rate": 0.18}	f	f
2733	TAX_GROUP	Tax Group	GST-free non-capital - 0%	tg7ig0JL47TA	2022-09-20 08:39:11.591963+00	2022-09-20 08:39:11.591995+00	1	\N	{"tax_rate": 0.28}	f	f
2734	TAX_GROUP	Tax Group	Pant Tax @0%	tg7JTybZgV72	2022-09-20 08:39:11.592078+00	2022-09-20 08:39:11.592109+00	1	\N	{"tax_rate": 0.0}	f	f
2735	TAX_GROUP	Tax Group	NVV6A35DEB	tg7MUaF3jn8g	2022-09-20 08:39:11.592181+00	2022-09-20 08:39:11.592204+00	1	\N	{"tax_rate": 0.18}	f	f
3128	MERCHANT	Merchant	Wal-Mart	852	2022-09-20 08:40:15.993087+00	2022-09-20 08:40:15.993146+00	1	\N	\N	f	f
2736	TAX_GROUP	Tax Group	ERWLSCCF5Y	tg7nwnwdF4dT	2022-09-20 08:39:11.592283+00	2022-09-20 08:39:11.592313+00	1	\N	{"tax_rate": 0.18}	f	f
2738	TAX_GROUP	Tax Group	UNDEF-AU @0.0%	tg7TABrTPI9Y	2022-09-20 08:39:11.592493+00	2022-09-20 08:39:11.592522+00	1	\N	{"tax_rate": 0.0}	f	f
2739	TAX_GROUP	Tax Group	3TBA1Y8XTJ	tg82dF3hhe5n	2022-09-20 08:39:11.592597+00	2022-09-20 08:39:11.592627+00	1	\N	{"tax_rate": 0.18}	f	f
2740	TAX_GROUP	Tax Group	asdads	tg8H1IYs5tK1	2022-09-20 08:39:11.5927+00	2022-09-20 08:39:11.59273+00	1	\N	{"tax_rate": 0.98}	f	f
2741	TAX_GROUP	Tax Group	XNNLG4CWVK	tg8hMa98dhaY	2022-09-20 08:39:11.592798+00	2022-09-20 08:39:11.592821+00	1	\N	{"tax_rate": 0.18}	f	f
2742	TAX_GROUP	Tax Group	XEC9NORGDY	tg8KRs4k8dzZ	2022-09-20 08:39:11.625617+00	2022-09-20 08:39:11.625706+00	1	\N	{"tax_rate": 0.18}	f	f
2743	TAX_GROUP	Tax Group	GST on capital - 10%	tg8NsXbzhPL9	2022-09-20 08:39:11.625904+00	2022-09-20 08:39:11.625974+00	1	\N	{"tax_rate": 0.28}	f	f
2744	TAX_GROUP	Tax Group	G5HSJNY9V8	tg8u6LIgEveF	2022-09-20 08:39:11.626184+00	2022-09-20 08:39:11.626355+00	1	\N	{"tax_rate": 0.18}	f	f
2748	TAX_GROUP	Tax Group	13GI6S3UYN	tga0lMbZ6RBf	2022-09-20 08:39:11.632026+00	2022-09-20 08:39:11.632049+00	1	\N	{"tax_rate": 0.18}	f	f
2749	TAX_GROUP	Tax Group	AQB26CI4C2	tga8X5feRpon	2022-09-20 08:39:11.632113+00	2022-09-20 08:39:11.63215+00	1	\N	{"tax_rate": 0.18}	f	f
2750	TAX_GROUP	Tax Group	1PKB8P46QU	tga95PVTYDvs	2022-09-20 08:39:11.632329+00	2022-09-20 08:39:11.632354+00	1	\N	{"tax_rate": 0.18}	f	f
2752	TAX_GROUP	Tax Group	FDU2ZPCGV4	tgadQszc73ls	2022-09-20 08:39:11.632508+00	2022-09-20 08:39:11.632593+00	1	\N	{"tax_rate": 0.18}	f	f
3065	MERCHANT	Merchant	James Taylor	852	2022-09-20 08:40:15.859781+00	2022-09-20 08:40:15.85981+00	1	\N	\N	f	f
2753	TAX_GROUP	Tax Group	WRVEPSQLUO	tgaDUDX0wKfx	2022-09-20 08:39:11.632681+00	2022-09-20 08:39:11.632704+00	1	\N	{"tax_rate": 0.18}	f	f
2754	TAX_GROUP	Tax Group	QE0PQSDQPB	tgAfGyr9gLcC	2022-09-20 08:39:11.632777+00	2022-09-20 08:39:11.632807+00	1	\N	{"tax_rate": 0.18}	f	f
2755	TAX_GROUP	Tax Group	JVFYUUP52V	tgAGJvQftHOa	2022-09-20 08:39:11.632868+00	2022-09-20 08:39:11.63289+00	1	\N	{"tax_rate": 0.18}	f	f
2756	TAX_GROUP	Tax Group	6RTQSGGVBB	tgaitDrJ7HKX	2022-09-20 08:39:11.632953+00	2022-09-20 08:39:11.632973+00	1	\N	{"tax_rate": 0.18}	f	f
2757	TAX_GROUP	Tax Group	ABN: dfvdfvf @20.0%	tgaj9yDnx3V7	2022-09-20 08:39:11.633023+00	2022-09-20 08:39:11.633044+00	1	\N	{"tax_rate": 0.2}	f	f
2758	TAX_GROUP	Tax Group	SNB8I4896F	tgANllvJ4iN0	2022-09-20 08:39:11.633106+00	2022-09-20 08:39:11.633127+00	1	\N	{"tax_rate": 0.18}	f	f
2759	TAX_GROUP	Tax Group	GST: ADJ-AU @0.0%	tgArJ1XJSvQ1	2022-09-20 08:39:11.633197+00	2022-09-20 08:39:11.633218+00	1	\N	{"tax_rate": 0.0}	f	f
2760	TAX_GROUP	Tax Group	95FDDT0ADR	tgArL90u46SV	2022-09-20 08:39:11.633269+00	2022-09-20 08:39:11.63329+00	1	\N	{"tax_rate": 0.18}	f	f
2761	TAX_GROUP	Tax Group	9Q25F572X1	tgauWe29lsRy	2022-09-20 08:39:11.63335+00	2022-09-20 08:39:11.633372+00	1	\N	{"tax_rate": 0.18}	f	f
2762	TAX_GROUP	Tax Group	RCYUA4VYHK	tgb5nFjKsyl6	2022-09-20 08:39:11.633638+00	2022-09-20 08:39:11.633668+00	1	\N	{"tax_rate": 0.18}	f	f
2763	TAX_GROUP	Tax Group	Nilesh Tax @10%	tgB8tkI8kkOV	2022-09-20 08:39:11.633731+00	2022-09-20 08:39:11.633753+00	1	\N	{"tax_rate": 0.1}	f	f
2764	TAX_GROUP	Tax Group	DM7138IDE2	tgB8X2Wlujvd	2022-09-20 08:39:11.633823+00	2022-09-20 08:39:11.633852+00	1	\N	{"tax_rate": 0.18}	f	f
2765	TAX_GROUP	Tax Group	DWU8MKBQEV	tgb9lp7pgKro	2022-09-20 08:39:11.633941+00	2022-09-20 08:39:11.634+00	1	\N	{"tax_rate": 0.18}	f	f
2766	TAX_GROUP	Tax Group	9R407O18OU	tgbbjo87dXZh	2022-09-20 08:39:11.634073+00	2022-09-20 08:39:11.634106+00	1	\N	{"tax_rate": 0.18}	f	f
2767	TAX_GROUP	Tax Group	WUZT4BLA9Z	tgbCmfy69LBW	2022-09-20 08:39:11.634173+00	2022-09-20 08:39:11.634195+00	1	\N	{"tax_rate": 0.18}	f	f
2768	TAX_GROUP	Tax Group	747DS1JYZB	tgBDWcnUMBpx	2022-09-20 08:39:11.634418+00	2022-09-20 08:39:11.634442+00	1	\N	{"tax_rate": 0.18}	f	f
2769	TAX_GROUP	Tax Group	9GO0WXN6RN	tgBFrF9ipSCf	2022-09-20 08:39:11.634496+00	2022-09-20 08:39:11.634517+00	1	\N	{"tax_rate": 0.18}	f	f
2770	TAX_GROUP	Tax Group	X6T4RNW4II	tgBJW9eEDGUk	2022-09-20 08:39:11.634587+00	2022-09-20 08:39:11.634616+00	1	\N	{"tax_rate": 0.18}	f	f
2771	TAX_GROUP	Tax Group	AZMVYWZ7BW	tgBkiVZxAEj8	2022-09-20 08:39:11.634935+00	2022-09-20 08:39:11.634963+00	1	\N	{"tax_rate": 0.18}	f	f
2772	TAX_GROUP	Tax Group	EY28M1P22T	tgBQGdEkPr4j	2022-09-20 08:39:11.635039+00	2022-09-20 08:39:11.635062+00	1	\N	{"tax_rate": 0.18}	f	f
2773	TAX_GROUP	Tax Group	OYSLBGDVDT	tgBqKL4ngl1b	2022-09-20 08:39:11.635123+00	2022-09-20 08:39:11.635143+00	1	\N	{"tax_rate": 0.18}	f	f
2774	TAX_GROUP	Tax Group	XKZTXD6J07	tgbwF76xZ6Pb	2022-09-20 08:39:11.635194+00	2022-09-20 08:39:11.635215+00	1	\N	{"tax_rate": 0.18}	f	f
2775	TAX_GROUP	Tax Group	GST on capital @0%	tgbyQDWdp4HT	2022-09-20 08:39:11.635439+00	2022-09-20 08:39:11.63546+00	1	\N	{"tax_rate": 0.0}	f	f
2776	TAX_GROUP	Tax Group	OPUXX1NWJD	tgbzkdxqhtI1	2022-09-20 08:39:11.635515+00	2022-09-20 08:39:11.635536+00	1	\N	{"tax_rate": 0.18}	f	f
2777	TAX_GROUP	Tax Group	JYJHRR8B69	tgBZmftPpxAj	2022-09-20 08:39:11.635596+00	2022-09-20 08:39:11.635618+00	1	\N	{"tax_rate": 0.18}	f	f
2778	TAX_GROUP	Tax Group	GST on non-capital @10%	tgbzwu7Cka9M	2022-09-20 08:39:11.635679+00	2022-09-20 08:39:11.635701+00	1	\N	{"tax_rate": 0.1}	f	f
2779	TAX_GROUP	Tax Group	DEL4M6NRFW	tgC1lqWVovlW	2022-09-20 08:39:11.635761+00	2022-09-20 08:39:11.635782+00	1	\N	{"tax_rate": 0.18}	f	f
2780	TAX_GROUP	Tax Group	GST CA_0 @0.0%	tgc1rvIT6Bn1	2022-09-20 08:39:11.635844+00	2022-09-20 08:39:11.63587+00	1	\N	{"tax_rate": 0.0}	f	f
2781	TAX_GROUP	Tax Group	GST-free capital @0%	tgCfp1fUBdlX	2022-09-20 08:39:11.63593+00	2022-09-20 08:39:11.635949+00	1	\N	{"tax_rate": 0}	f	f
2782	TAX_GROUP	Tax Group	R92514U6N6	tgCuuwwIlvFm	2022-09-20 08:39:11.636001+00	2022-09-20 08:39:11.636022+00	1	\N	{"tax_rate": 0.18}	f	f
2783	TAX_GROUP	Tax Group	JDDDN0IM2E	tgcViap8gGOb	2022-09-20 08:39:11.636083+00	2022-09-20 08:39:11.636104+00	1	\N	{"tax_rate": 0.18}	f	f
2784	TAX_GROUP	Tax Group	OJ1ZB2W1AT	tgCW6oVxRh8S	2022-09-20 08:39:11.636164+00	2022-09-20 08:39:11.636184+00	1	\N	{"tax_rate": 0.18}	f	f
2785	TAX_GROUP	Tax Group	tax for sample @20.0%	tgD359VCOO4k	2022-09-20 08:39:11.636236+00	2022-09-20 08:39:11.636256+00	1	\N	{"tax_rate": 0.2}	f	f
2786	TAX_GROUP	Tax Group	LF3OR9B6UY	tgD4DZltfZm2	2022-09-20 08:39:11.636316+00	2022-09-20 08:39:11.636336+00	1	\N	{"tax_rate": 0.18}	f	f
2787	TAX_GROUP	Tax Group	ZSGKDU3OLB	tgd9jRwuVJ50	2022-09-20 08:39:11.636517+00	2022-09-20 08:39:11.636547+00	1	\N	{"tax_rate": 0.18}	f	f
3044	MERCHANT	Merchant	Labhvam	852	2022-09-20 08:40:15.786215+00	2022-09-20 08:40:15.786245+00	1	\N	\N	f	f
2788	TAX_GROUP	Tax Group	GST: UNDEF-AU @0.0%	tgdDcmqveXjC	2022-09-20 08:39:11.636612+00	2022-09-20 08:39:11.636633+00	1	\N	{"tax_rate": 0.0}	f	f
2789	TAX_GROUP	Tax Group	2WN3XRLS6H	tgddYlDJNOG9	2022-09-20 08:39:11.636704+00	2022-09-20 08:39:11.636724+00	1	\N	{"tax_rate": 0.18}	f	f
2790	TAX_GROUP	Tax Group	X4R0A458J3	tgdhExksqrBU	2022-09-20 08:39:11.636785+00	2022-09-20 08:39:11.636806+00	1	\N	{"tax_rate": 0.18}	f	f
2791	TAX_GROUP	Tax Group	Tax Exempt @0.0%	tgDHGmUj9YR8	2022-09-20 08:39:11.636866+00	2022-09-20 08:39:11.636887+00	1	\N	{"tax_rate": 0.0}	f	f
2792	TAX_GROUP	Tax Group	WGGUO7Z1SM	tgDHZqtOy6SU	2022-09-20 08:39:11.652543+00	2022-09-20 08:39:11.652583+00	1	\N	{"tax_rate": 0.18}	f	f
2793	TAX_GROUP	Tax Group	GST on non-capital @0%	tgdIMfh7iBOY	2022-09-20 08:39:11.652663+00	2022-09-20 08:39:11.652684+00	1	\N	{"tax_rate": 0.0}	f	f
2794	TAX_GROUP	Tax Group	LOITUJ2M1M	tgdIrsy8qgoa	2022-09-20 08:39:11.652744+00	2022-09-20 08:39:11.652764+00	1	\N	{"tax_rate": 0.18}	f	f
2795	TAX_GROUP	Tax Group	tax for jadu @20.0%	tgDiZoAy3aEI	2022-09-20 08:39:11.652823+00	2022-09-20 08:39:11.652846+00	1	\N	{"tax_rate": 0.2}	f	f
2796	TAX_GROUP	Tax Group	JVRYCPUK0F	tgdkgz4vv1Vl	2022-09-20 08:39:11.652916+00	2022-09-20 08:39:11.652936+00	1	\N	{"tax_rate": 0.18}	f	f
2797	TAX_GROUP	Tax Group	P9T0IITI3Q	tgdLysSnSLox	2022-09-20 08:39:11.652986+00	2022-09-20 08:39:11.653008+00	1	\N	{"tax_rate": 0.18}	f	f
2798	TAX_GROUP	Tax Group	VL45IRZHOK	tgdVMTXRNYu4	2022-09-20 08:39:11.653079+00	2022-09-20 08:39:11.6531+00	1	\N	{"tax_rate": 0.18}	f	f
2799	TAX_GROUP	Tax Group	RYHQGEPACZ	tgEAoIczkucD	2022-09-20 08:39:11.653159+00	2022-09-20 08:39:11.653179+00	1	\N	{"tax_rate": 0.18}	f	f
2800	TAX_GROUP	Tax Group	F0YGCWO5PP	tgEnkccvnY4e	2022-09-20 08:39:11.65323+00	2022-09-20 08:39:11.653251+00	1	\N	{"tax_rate": 0.18}	f	f
2801	TAX_GROUP	Tax Group	GST-free non-capital @0%	tgEru6wFHTM1	2022-09-20 08:39:11.653311+00	2022-09-20 08:39:11.653331+00	1	\N	{"tax_rate": 0}	f	f
2802	TAX_GROUP	Tax Group	NXPD1U8GHJ	tgERw1lWZaah	2022-09-20 08:39:11.653524+00	2022-09-20 08:39:11.653557+00	1	\N	{"tax_rate": 0.18}	f	f
2803	TAX_GROUP	Tax Group	VAT: Wow Tax @10.0%	tgEvaHjrKvx0	2022-09-20 08:39:11.653634+00	2022-09-20 08:39:11.653667+00	1	\N	{"tax_rate": 0.1}	f	f
2804	TAX_GROUP	Tax Group	560RKMO5QW	tgEYHASLyE0E	2022-09-20 08:39:11.653744+00	2022-09-20 08:39:11.653773+00	1	\N	{"tax_rate": 0.18}	f	f
2805	TAX_GROUP	Tax Group	GST: NA-AU @0.0%	tgf07hNu2f1L	2022-09-20 08:39:11.653847+00	2022-09-20 08:39:11.653878+00	1	\N	{"tax_rate": 0.0}	f	f
2806	TAX_GROUP	Tax Group	RHTSGJD4CV	tgf3cJ2q7Nqu	2022-09-20 08:39:11.653953+00	2022-09-20 08:39:11.653983+00	1	\N	{"tax_rate": 0.18}	f	f
2807	TAX_GROUP	Tax Group	CM556CRMO4	tgF7aZMGwdwa	2022-09-20 08:39:11.654064+00	2022-09-20 08:39:11.65409+00	1	\N	{"tax_rate": 0.18}	f	f
2808	TAX_GROUP	Tax Group	Y7ALNUN1XP	tgF9CJBTx6P9	2022-09-20 08:39:11.654175+00	2022-09-20 08:39:11.654385+00	1	\N	{"tax_rate": 0.18}	f	f
2809	TAX_GROUP	Tax Group	GST/HST: GST CA_5 @5.0%	tgFB3d6A5Nkf	2022-09-20 08:39:11.654473+00	2022-09-20 08:39:11.654496+00	1	\N	{"tax_rate": 0.05}	f	f
2810	TAX_GROUP	Tax Group	PZTO6DMVX2	tgFcheI45FJW	2022-09-20 08:39:11.654609+00	2022-09-20 08:39:11.654641+00	1	\N	{"tax_rate": 0.18}	f	f
2811	TAX_GROUP	Tax Group	NA-AU @0.0%	tgfMjmXkDsTx	2022-09-20 08:39:11.654708+00	2022-09-20 08:39:11.65472+00	1	\N	{"tax_rate": 0.0}	f	f
2812	TAX_GROUP	Tax Group	GST: EXPS-AU @0.0%	tgFQkkQOPT8i	2022-09-20 08:39:11.654782+00	2022-09-20 08:39:11.654805+00	1	\N	{"tax_rate": 0.0}	f	f
2813	TAX_GROUP	Tax Group	QXWLZB6RGO	tgfuGOalhfh1	2022-09-20 08:39:11.654878+00	2022-09-20 08:39:11.654909+00	1	\N	{"tax_rate": 0.18}	f	f
2814	TAX_GROUP	Tax Group	CPF-AU @0.0%	tgfZhOK0QWKu	2022-09-20 08:39:11.654982+00	2022-09-20 08:39:11.655005+00	1	\N	{"tax_rate": 0.0}	f	f
2815	TAX_GROUP	Tax Group	GST: NCI-AU @0.0%	tgG1mnAzZEit	2022-09-20 08:39:11.655076+00	2022-09-20 08:39:11.655107+00	1	\N	{"tax_rate": 0.0}	f	f
2816	TAX_GROUP	Tax Group	ZDM9M85NEK	tgg35A74tQRN	2022-09-20 08:39:11.655302+00	2022-09-20 08:39:11.655343+00	1	\N	{"tax_rate": 0.18}	f	f
2817	TAX_GROUP	Tax Group	MGCYQRWOJ8	tggb3nrVbdnw	2022-09-20 08:39:11.655417+00	2022-09-20 08:39:11.655438+00	1	\N	{"tax_rate": 0.18}	f	f
2818	TAX_GROUP	Tax Group	2CSL18LRX5	tgGE1ZWX2cgF	2022-09-20 08:39:11.655508+00	2022-09-20 08:39:11.655539+00	1	\N	{"tax_rate": 0.18}	f	f
2819	TAX_GROUP	Tax Group	XZXC2AN5UM	tgGedy1BnUMN	2022-09-20 08:39:11.655613+00	2022-09-20 08:39:11.655642+00	1	\N	{"tax_rate": 0.18}	f	f
2820	TAX_GROUP	Tax Group	WET: WET-AU @29.0%	tggmh4xFPIrY	2022-09-20 08:39:11.655726+00	2022-09-20 08:39:11.655756+00	1	\N	{"tax_rate": 0.29}	f	f
2821	TAX_GROUP	Tax Group	5VD52OUE8G	tgGMJFyqFBD0	2022-09-20 08:39:11.655821+00	2022-09-20 08:39:11.655841+00	1	\N	{"tax_rate": 0.18}	f	f
2823	TAX_GROUP	Tax Group	WQAYU3EVN9	tggps3ozYWXc	2022-09-20 08:39:11.656015+00	2022-09-20 08:39:11.656035+00	1	\N	{"tax_rate": 0.18}	f	f
2824	TAX_GROUP	Tax Group	GST CA_E @0.0%	tggQgp1T8mNX	2022-09-20 08:39:11.656156+00	2022-09-20 08:39:11.656311+00	1	\N	{"tax_rate": 0.0}	f	f
2825	TAX_GROUP	Tax Group	GST-free capital - 0%	tggu76WXIdjY	2022-09-20 08:39:11.656416+00	2022-09-20 08:39:11.656436+00	1	\N	{"tax_rate": 0.28}	f	f
679	PROJECT	Project	Project 3	203311	2022-09-20 08:39:06.848527+00	2022-09-20 08:39:06.848647+00	1	t	\N	f	f
2826	TAX_GROUP	Tax Group	M0P4RTHRRA	tgh43w8fzs1b	2022-09-20 08:39:11.656508+00	2022-09-20 08:39:11.656538+00	1	\N	{"tax_rate": 0.18}	f	f
2827	TAX_GROUP	Tax Group	GST: CPI-AU @0.0%	tgHbN222yK8n	2022-09-20 08:39:11.656602+00	2022-09-20 08:39:11.656624+00	1	\N	{"tax_rate": 0.0}	f	f
2828	TAX_GROUP	Tax Group	FYW3N2Z4G1	tgHiZcokwwZX	2022-09-20 08:39:11.656709+00	2022-09-20 08:39:11.656739+00	1	\N	{"tax_rate": 0.18}	f	f
2829	TAX_GROUP	Tax Group	GSTv21	tghOBz9yODLz	2022-09-20 08:39:11.656813+00	2022-09-20 08:39:11.656843+00	1	\N	{"tax_rate": 0.18}	f	f
2830	TAX_GROUP	Tax Group	tax for zero @0.0%	tgHOHGJBB9Oi	2022-09-20 08:39:11.656913+00	2022-09-20 08:39:11.656932+00	1	\N	{"tax_rate": 0.0}	f	f
2831	TAX_GROUP	Tax Group	T5G8M4IVT8	tgHsUgpvwEAv	2022-09-20 08:39:11.656995+00	2022-09-20 08:39:11.657018+00	1	\N	{"tax_rate": 0.18}	f	f
2832	TAX_GROUP	Tax Group	GLBTYBKH0W	tgHUR0p5j9MU	2022-09-20 08:39:11.657101+00	2022-09-20 08:39:11.657138+00	1	\N	{"tax_rate": 0.18}	f	f
2833	TAX_GROUP	Tax Group	Q230CP6HS8	tghVa6A2bxhj	2022-09-20 08:39:11.65733+00	2022-09-20 08:39:11.657362+00	1	\N	{"tax_rate": 0.18}	f	f
178	CATEGORY	Category	Legal	135913	2022-09-20 08:39:03.451678+00	2022-09-20 08:39:03.451707+00	1	t	\N	f	f
2835	TAX_GROUP	Tax Group	tax for ten @10.0%	tghYeIKavACw	2022-09-20 08:39:11.657514+00	2022-09-20 08:39:11.657526+00	1	\N	{"tax_rate": 0.1}	f	f
2836	TAX_GROUP	Tax Group	Exempt Sales @0.0%	tghz8Mq9SXTg	2022-09-20 08:39:11.657585+00	2022-09-20 08:39:11.657618+00	1	\N	{"tax_rate": 0.0}	f	f
2837	TAX_GROUP	Tax Group	M75YLYFLX2	tgIbiM63m7mV	2022-09-20 08:39:11.657739+00	2022-09-20 08:39:11.657769+00	1	\N	{"tax_rate": 0.18}	f	f
2838	TAX_GROUP	Tax Group	D1A81KCH82	tgIdDHOoKVzm	2022-09-20 08:39:11.65784+00	2022-09-20 08:39:11.657875+00	1	\N	{"tax_rate": 0.18}	f	f
2839	TAX_GROUP	Tax Group	RBJU6PV6UZ	tgIIYAOtOZ8o	2022-09-20 08:39:11.658003+00	2022-09-20 08:39:11.658025+00	1	\N	{"tax_rate": 0.18}	f	f
2841	TAX_GROUP	Tax Group	Q17J4DV6PY	tgiuRUp65soc	2022-09-20 08:39:11.658285+00	2022-09-20 08:39:11.659648+00	1	\N	{"tax_rate": 0.18}	f	f
2842	TAX_GROUP	Tax Group	CA-PST-AB @0.0%	tgiYnjwl2RtN	2022-09-20 08:39:11.672814+00	2022-09-20 08:39:11.672843+00	1	\N	{"tax_rate": 0.0}	f	f
2843	TAX_GROUP	Tax Group	GST: ITS-AU @0.0%	tgIyxnneqKm4	2022-09-20 08:39:11.672896+00	2022-09-20 08:39:11.672916+00	1	\N	{"tax_rate": 0.0}	f	f
2844	TAX_GROUP	Tax Group	QDJ8J2CPWA	tgizQ5b2qmlO	2022-09-20 08:39:11.672976+00	2022-09-20 08:39:11.672997+00	1	\N	{"tax_rate": 0.18}	f	f
2845	TAX_GROUP	Tax Group	GST: NCT-AU @10.0%	tgj97Eu6lEE3	2022-09-20 08:39:11.673059+00	2022-09-20 08:39:11.673079+00	1	\N	{"tax_rate": 0.1}	f	f
2846	TAX_GROUP	Tax Group	09ZKNVZ4O6	tgjAsjDeXCpN	2022-09-20 08:39:11.67314+00	2022-09-20 08:39:11.67316+00	1	\N	{"tax_rate": 0.18}	f	f
2847	TAX_GROUP	Tax Group	NCI-AU @0.0%	tgJD4Xo7hCep	2022-09-20 08:39:11.673221+00	2022-09-20 08:39:11.673241+00	1	\N	{"tax_rate": 0.0}	f	f
2848	TAX_GROUP	Tax Group	HTR8W6D3JR	tgjFfmEfMnki	2022-09-20 08:39:11.673302+00	2022-09-20 08:39:11.673322+00	1	\N	{"tax_rate": 0.18}	f	f
2849	TAX_GROUP	Tax Group	RMLZWIV6W7	tgJkpUDaCB6c	2022-09-20 08:39:11.673374+00	2022-09-20 08:39:11.673546+00	1	\N	{"tax_rate": 0.18}	f	f
2850	TAX_GROUP	Tax Group	USD4J624GO	tgjodMdR3Ag2	2022-09-20 08:39:11.673736+00	2022-09-20 08:39:11.673763+00	1	\N	{"tax_rate": 0.18}	f	f
2851	TAX_GROUP	Tax Group	PST_AB_0 @0.0%	tgjtVTJhrY3p	2022-09-20 08:39:11.673815+00	2022-09-20 08:39:11.673834+00	1	\N	{"tax_rate": 0.0}	f	f
2852	TAX_GROUP	Tax Group	T5AOOEOIMJ	tgjYXrePWshl	2022-09-20 08:39:11.673887+00	2022-09-20 08:39:11.673898+00	1	\N	{"tax_rate": 0.18}	f	f
2853	TAX_GROUP	Tax Group	ADJ-AU @0.0%	tgjzLEqLJLru	2022-09-20 08:39:11.673949+00	2022-09-20 08:39:11.67397+00	1	\N	{"tax_rate": 0.0}	f	f
2854	TAX_GROUP	Tax Group	4CF762Q721	tgk3oVtid3iD	2022-09-20 08:39:11.674031+00	2022-09-20 08:39:11.674052+00	1	\N	{"tax_rate": 0.18}	f	f
2855	TAX_GROUP	Tax Group	27Z4X2C201	tgKjEijcJFBE	2022-09-20 08:39:11.674113+00	2022-09-20 08:39:11.674133+00	1	\N	{"tax_rate": 0.18}	f	f
2856	TAX_GROUP	Tax Group	DJJWB6F4HM	tgKNmUyduTjf	2022-09-20 08:39:11.674185+00	2022-09-20 08:39:11.674204+00	1	\N	{"tax_rate": 0.18}	f	f
2858	TAX_GROUP	Tax Group	Z9EDD2VZC3	tgKSmIhciv9X	2022-09-20 08:39:11.674456+00	2022-09-20 08:39:11.674487+00	1	\N	{"tax_rate": 0.18}	f	f
2859	TAX_GROUP	Tax Group	BEOCQYS8EN	tgKwbHu63m6h	2022-09-20 08:39:11.674558+00	2022-09-20 08:39:11.674585+00	1	\N	{"tax_rate": 0.18}	f	f
2860	TAX_GROUP	Tax Group	VPJJOTDBCR	tgl4w9N3rm96	2022-09-20 08:39:11.674648+00	2022-09-20 08:39:11.674679+00	1	\N	{"tax_rate": 0.18}	f	f
2861	TAX_GROUP	Tax Group	LQEK36KCCF	tgL8ZiWvtrdS	2022-09-20 08:39:11.674778+00	2022-09-20 08:39:11.674808+00	1	\N	{"tax_rate": 0.18}	f	f
2862	TAX_GROUP	Tax Group	8ZUVNA95N1	tglCpwEHWoSk	2022-09-20 08:39:11.674916+00	2022-09-20 08:39:11.674944+00	1	\N	{"tax_rate": 0.18}	f	f
2863	TAX_GROUP	Tax Group	YO63CHLCBF	tglCtjyXrqTs	2022-09-20 08:39:11.674999+00	2022-09-20 08:39:11.67502+00	1	\N	{"tax_rate": 0.18}	f	f
2864	TAX_GROUP	Tax Group	R6KJ5YA4U9	tgLftvQ4yM0m	2022-09-20 08:39:11.675091+00	2022-09-20 08:39:11.675116+00	1	\N	{"tax_rate": 0.18}	f	f
2865	TAX_GROUP	Tax Group	GST on non-capital - 10%	tgLgjZDkBHOX	2022-09-20 08:39:11.675177+00	2022-09-20 08:39:11.675575+00	1	\N	{"tax_rate": 0.28}	f	f
2866	TAX_GROUP	Tax Group	O4Z369SVSU	tgLhjywOOpvH	2022-09-20 08:39:11.6758+00	2022-09-20 08:39:11.675834+00	1	\N	{"tax_rate": 0.18}	f	f
2867	TAX_GROUP	Tax Group	UX47SL7LOE	tgLHqwTlJ7cv	2022-09-20 08:39:11.675939+00	2022-09-20 08:39:11.675965+00	1	\N	{"tax_rate": 0.18}	f	f
2868	TAX_GROUP	Tax Group	GSTv2	tglItKJPWBfD	2022-09-20 08:39:11.676064+00	2022-09-20 08:39:11.676093+00	1	\N	{"tax_rate": 0.18}	f	f
2870	TAX_GROUP	Tax Group	611ZFAT5SM	tgLMpEVQmvzR	2022-09-20 08:39:11.676368+00	2022-09-20 08:39:11.676396+00	1	\N	{"tax_rate": 0.18}	f	f
2871	TAX_GROUP	Tax Group	Nilesh Tax @0%	tglmrXAQ8A5f	2022-09-20 08:39:11.676458+00	2022-09-20 08:39:11.67648+00	1	\N	{"tax_rate": 0.0}	f	f
2872	TAX_GROUP	Tax Group	9SI9Y9A036	tglnSdoifDoA	2022-09-20 08:39:11.676712+00	2022-09-20 08:39:11.676814+00	1	\N	{"tax_rate": 0.18}	f	f
2874	TAX_GROUP	Tax Group	OW43OS7WUO	tgLYWgsbLTpG	2022-09-20 08:39:11.676991+00	2022-09-20 08:39:11.67703+00	1	\N	{"tax_rate": 0.18}	f	f
2876	TAX_GROUP	Tax Group	CD5C1P0EBC	tgmANuJ1Lyyw	2022-09-20 08:39:11.677346+00	2022-09-20 08:39:11.677361+00	1	\N	{"tax_rate": 0.18}	f	f
2877	TAX_GROUP	Tax Group	5JHCVQD5SS	tgmEH8tzx7Fs	2022-09-20 08:39:11.677415+00	2022-09-20 08:39:11.677436+00	1	\N	{"tax_rate": 0.18}	f	f
2878	TAX_GROUP	Tax Group	03QBRUQL9Y	tgMJPwgwqLjl	2022-09-20 08:39:11.677732+00	2022-09-20 08:39:11.677764+00	1	\N	{"tax_rate": 0.18}	f	f
2879	TAX_GROUP	Tax Group	LCU8INQONN	tgMMC9y7yZLa	2022-09-20 08:39:11.677841+00	2022-09-20 08:39:11.677864+00	1	\N	{"tax_rate": 0.18}	f	f
2880	TAX_GROUP	Tax Group	CA-S-ON @0.0%	tgMn3pe1xFXO	2022-09-20 08:39:11.677928+00	2022-09-20 08:39:11.678316+00	1	\N	{"tax_rate": 0.0}	f	f
2881	TAX_GROUP	Tax Group	DWK2H94RM7	tgMslNJflABK	2022-09-20 08:39:11.678522+00	2022-09-20 08:39:11.678542+00	1	\N	{"tax_rate": 0.18}	f	f
2882	TAX_GROUP	Tax Group	WFRIUTX9C7	tgMu6kwxCgQ5	2022-09-20 08:39:11.678663+00	2022-09-20 08:39:11.67869+00	1	\N	{"tax_rate": 0.18}	f	f
2883	TAX_GROUP	Tax Group	6OJKRIJ9CD	tgmyCZ1JPg4G	2022-09-20 08:39:11.678745+00	2022-09-20 08:39:11.678802+00	1	\N	{"tax_rate": 0.18}	f	f
3078	MERCHANT	Merchant	Robertson & Associates	852	2022-09-20 08:40:15.889211+00	2022-09-20 08:40:15.889253+00	1	\N	\N	f	f
2885	TAX_GROUP	Tax Group	County: New York County @1.5%	tgn16RsBIa8O	2022-09-20 08:39:11.678974+00	2022-09-20 08:39:11.678995+00	1	\N	{"tax_rate": 0.01}	f	f
2886	TAX_GROUP	Tax Group	M8MES6DZKB	tgn18EUCd2TJ	2022-09-20 08:39:11.679057+00	2022-09-20 08:39:11.679077+00	1	\N	{"tax_rate": 0.18}	f	f
2887	TAX_GROUP	Tax Group	UTJEMXABWZ	tgN1c7PcZnTf	2022-09-20 08:39:11.679163+00	2022-09-20 08:39:11.679183+00	1	\N	{"tax_rate": 0.18}	f	f
2888	TAX_GROUP	Tax Group	6HEKYZATT2	tgN2DNgkzL1Q	2022-09-20 08:39:11.679263+00	2022-09-20 08:39:11.679283+00	1	\N	{"tax_rate": 0.18}	f	f
2889	TAX_GROUP	Tax Group	VACMTQNMYJ	tgNaVPIVhRk7	2022-09-20 08:39:11.679365+00	2022-09-20 08:39:11.680773+00	1	\N	{"tax_rate": 0.18}	f	f
2890	TAX_GROUP	Tax Group	VAT	tgnci8BWh2e2	2022-09-20 08:39:11.68124+00	2022-09-20 08:39:11.681428+00	1	\N	{"tax_rate": 0.1}	f	f
2891	TAX_GROUP	Tax Group	PO4UXUPB2Z	tgNDXVEuaGj4	2022-09-20 08:39:11.68155+00	2022-09-20 08:39:11.681577+00	1	\N	{"tax_rate": 0.18}	f	f
2892	TAX_GROUP	Tax Group	1A8A84WBA2	tgnGUH2NVrEA	2022-09-20 08:39:11.972666+00	2022-09-20 08:39:11.972784+00	1	\N	{"tax_rate": 0.18}	f	f
2894	TAX_GROUP	Tax Group	I4XUSD23KB	tgnvrN8trjBP	2022-09-20 08:39:11.973165+00	2022-09-20 08:39:11.973383+00	1	\N	{"tax_rate": 0.18}	f	f
2895	TAX_GROUP	Tax Group	TFS-AU @0.0%	tgO2rqAAcZTd	2022-09-20 08:39:11.973581+00	2022-09-20 08:39:11.973624+00	1	\N	{"tax_rate": 0.0}	f	f
2896	TAX_GROUP	Tax Group	GST: CPF-AU @0.0%	tgO8oQwXP01L	2022-09-20 08:39:11.973704+00	2022-09-20 08:39:11.973778+00	1	\N	{"tax_rate": 0.0}	f	f
2897	TAX_GROUP	Tax Group	Q5OGEJBTKM	tgoAmASNRgzk	2022-09-20 08:39:11.973874+00	2022-09-20 08:39:11.973904+00	1	\N	{"tax_rate": 0.18}	f	f
2898	TAX_GROUP	Tax Group	DSA93VPG9K	tgoExVlpnnbM	2022-09-20 08:39:11.973988+00	2022-09-20 08:39:11.974109+00	1	\N	{"tax_rate": 0.18}	f	f
2899	TAX_GROUP	Tax Group	EXPS-AU @0.0%	tgoGDuG6OMEa	2022-09-20 08:39:11.974208+00	2022-09-20 08:39:11.974239+00	1	\N	{"tax_rate": 0.0}	f	f
2900	TAX_GROUP	Tax Group	VAT: UK Tax @10.0%	tgogXSf1onY0	2022-09-20 08:39:11.97432+00	2022-09-20 08:39:11.974347+00	1	\N	{"tax_rate": 0.1}	f	f
2901	TAX_GROUP	Tax Group	II6NWV8PK4	tgoGzqpXD02A	2022-09-20 08:39:11.974678+00	2022-09-20 08:39:11.974761+00	1	\N	{"tax_rate": 0.18}	f	f
2902	TAX_GROUP	Tax Group	TG1OG645TP	tgoiydGXa6RI	2022-09-20 08:39:11.97495+00	2022-09-20 08:39:11.975021+00	1	\N	{"tax_rate": 0.18}	f	f
2903	TAX_GROUP	Tax Group	GP2UXTORT6	tgoK6ws8L40m	2022-09-20 08:39:11.975179+00	2022-09-20 08:39:11.975227+00	1	\N	{"tax_rate": 0.18}	f	f
2904	TAX_GROUP	Tax Group	H4FLZPRDRU	tgoRFNG0JKDV	2022-09-20 08:39:11.975596+00	2022-09-20 08:39:11.975747+00	1	\N	{"tax_rate": 0.18}	f	f
2906	TAX_GROUP	Tax Group	PNSOA0VKSF	tgOvm9YaBGPa	2022-09-20 08:39:11.975955+00	2022-09-20 08:39:11.975985+00	1	\N	{"tax_rate": 0.18}	f	f
2907	TAX_GROUP	Tax Group	6QLNH6Y4UM	tgoWBF2LV1DY	2022-09-20 08:39:11.976064+00	2022-09-20 08:39:11.976092+00	1	\N	{"tax_rate": 0.18}	f	f
2908	TAX_GROUP	Tax Group	Input tax - 0%	tgP2csYPZYr1	2022-09-20 08:39:11.976158+00	2022-09-20 08:39:11.976185+00	1	\N	{"tax_rate": 0.28}	f	f
2910	TAX_GROUP	Tax Group	QHGZ8OB0QW	tgp7Hi8kNwiw	2022-09-20 08:39:11.976465+00	2022-09-20 08:39:11.97651+00	1	\N	{"tax_rate": 0.18}	f	f
2911	TAX_GROUP	Tax Group	GG10QAP2S5	tgP8qUkLoAcJ	2022-09-20 08:39:11.976611+00	2022-09-20 08:39:11.976641+00	1	\N	{"tax_rate": 0.18}	f	f
2912	TAX_GROUP	Tax Group	1NIPCD4AIV	tgPBQtd1JY9j	2022-09-20 08:39:11.976724+00	2022-09-20 08:39:11.976753+00	1	\N	{"tax_rate": 0.18}	f	f
2913	TAX_GROUP	Tax Group	KF5LT1RF09	tgPDsE2wRsQz	2022-09-20 08:39:11.976831+00	2022-09-20 08:39:11.976858+00	1	\N	{"tax_rate": 0.18}	f	f
2914	TAX_GROUP	Tax Group	Tax on Consulting @8.25%	tgpgTQbdAQTE	2022-09-20 08:39:11.976924+00	2022-09-20 08:39:11.976951+00	1	\N	{"tax_rate": 0.08}	f	f
2915	TAX_GROUP	Tax Group	NCF-AU @0.0%	tgpIyPXp7YbJ	2022-09-20 08:39:11.977016+00	2022-09-20 08:39:11.977043+00	1	\N	{"tax_rate": 0.0}	f	f
2917	TAX_GROUP	Tax Group	9GZBIA2Z9H	tgPnK7or3K9x	2022-09-20 08:39:11.9772+00	2022-09-20 08:39:11.977227+00	1	\N	{"tax_rate": 0.18}	f	f
2918	TAX_GROUP	Tax Group	9KAP9QWA44	tgPOXTd5DoZ3	2022-09-20 08:39:11.977293+00	2022-09-20 08:39:11.97732+00	1	\N	{"tax_rate": 0.18}	f	f
2919	TAX_GROUP	Tax Group	Tax on Purchases @8.25%	tgPoY58NUJbl	2022-09-20 08:39:11.977523+00	2022-09-20 08:39:11.977562+00	1	\N	{"tax_rate": 0.08}	f	f
2920	TAX_GROUP	Tax Group	JQTAKMBYNJ	tgPs7otMgPlA	2022-09-20 08:39:11.977628+00	2022-09-20 08:39:11.977655+00	1	\N	{"tax_rate": 0.18}	f	f
2921	TAX_GROUP	Tax Group	O020KR52QV	tgPwj9u0NQHN	2022-09-20 08:39:11.97772+00	2022-09-20 08:39:11.977747+00	1	\N	{"tax_rate": 0.18}	f	f
2923	TAX_GROUP	Tax Group	Pant Tax @20%	tgq2mKV86LWz	2022-09-20 08:39:11.977905+00	2022-09-20 08:39:11.977933+00	1	\N	{"tax_rate": 0.2}	f	f
2924	TAX_GROUP	Tax Group	CA-E @0.0%	tgQC13IAQIR6	2022-09-20 08:39:11.977997+00	2022-09-20 08:39:11.978024+00	1	\N	{"tax_rate": 0.0}	f	f
2925	TAX_GROUP	Tax Group	K9ZTD8WVCG	tgqC2qkdsqic	2022-09-20 08:39:11.97809+00	2022-09-20 08:39:11.978117+00	1	\N	{"tax_rate": 0.18}	f	f
2926	TAX_GROUP	Tax Group	OT0WPR3LG1	tgqc7sfCgKPi	2022-09-20 08:39:11.978183+00	2022-09-20 08:39:11.97821+00	1	\N	{"tax_rate": 0.18}	f	f
2927	TAX_GROUP	Tax Group	YA65ILOGVV	tgqCwT8Q9Dsv	2022-09-20 08:39:11.978275+00	2022-09-20 08:39:11.978302+00	1	\N	{"tax_rate": 0.18}	f	f
2928	TAX_GROUP	Tax Group	VEU3R97JU6	tgQdlZoHLujH	2022-09-20 08:39:11.97849+00	2022-09-20 08:39:11.97853+00	1	\N	{"tax_rate": 0.18}	f	f
2929	TAX_GROUP	Tax Group	MQ3MHKG1JM	tgQf69ylVLyE	2022-09-20 08:39:11.978596+00	2022-09-20 08:39:11.978624+00	1	\N	{"tax_rate": 0.18}	f	f
2930	TAX_GROUP	Tax Group	8V1FTMOLVI	tgQfmwntIzWb	2022-09-20 08:39:11.978689+00	2022-09-20 08:39:11.978717+00	1	\N	{"tax_rate": 0.18}	f	f
2931	TAX_GROUP	Tax Group	AU1B8Y7TGS	tgqjARJIS7fE	2022-09-20 08:39:11.978782+00	2022-09-20 08:39:11.978809+00	1	\N	{"tax_rate": 0.18}	f	f
2932	TAX_GROUP	Tax Group	LW8V0C86U9	tgqJdKUbPCut	2022-09-20 08:39:11.978875+00	2022-09-20 08:39:11.978902+00	1	\N	{"tax_rate": 0.18}	f	f
2933	TAX_GROUP	Tax Group	-Not Taxable- @0.0%	tgQLIh7kwQc2	2022-09-20 08:39:11.97902+00	2022-09-20 08:39:11.979182+00	1	\N	{"tax_rate": 0.0}	f	f
2934	TAX_GROUP	Tax Group	ERLZ2WXGBY	tgqNfbt23hXF	2022-09-20 08:39:11.97927+00	2022-09-20 08:39:11.979297+00	1	\N	{"tax_rate": 0.18}	f	f
2935	TAX_GROUP	Tax Group	GST: ashwin_tax_code_1 @2.0%	tgqpMNwVNkyv	2022-09-20 08:39:11.979487+00	2022-09-20 08:39:11.979534+00	1	\N	{"tax_rate": 0.02}	f	f
2936	TAX_GROUP	Tax Group	5OJBS10VAC	tgRDxtr0jV61	2022-09-20 08:39:11.979661+00	2022-09-20 08:39:11.979705+00	1	\N	{"tax_rate": 0.18}	f	f
2937	TAX_GROUP	Tax Group	T1WP4WBELF	tgrEYpYAIhJh	2022-09-20 08:39:11.979922+00	2022-09-20 08:39:11.97996+00	1	\N	{"tax_rate": 0.18}	f	f
2938	TAX_GROUP	Tax Group	. @0.0%	tgrGkDS30KOf	2022-09-20 08:39:11.98027+00	2022-09-20 08:39:11.980328+00	1	\N	{"tax_rate": 0.0}	f	f
2940	TAX_GROUP	Tax Group	UNDEF-GB @0.0%	tgRieT5aVKOi	2022-09-20 08:39:11.981845+00	2022-09-20 08:39:11.981912+00	1	\N	{"tax_rate": 0.0}	f	f
2941	TAX_GROUP	Tax Group	City: New York City @0.5%	tgrihEBRsqmk	2022-09-20 08:39:11.982079+00	2022-09-20 08:39:11.982125+00	1	\N	{"tax_rate": 0.01}	f	f
2942	TAX_GROUP	Tax Group	W6RV83BFWU	tgril32Nl0pB	2022-09-20 08:39:11.988754+00	2022-09-20 08:39:11.988795+00	1	\N	{"tax_rate": 0.18}	f	f
2943	TAX_GROUP	Tax Group	Sales Tax on Imports @0.0%	tgrnS3h0Ruzg	2022-09-20 08:39:11.988864+00	2022-09-20 08:39:11.988892+00	1	\N	{"tax_rate": 0.0}	f	f
2944	TAX_GROUP	Tax Group	ABN: Nilesh @54.0%	tgRPkX7ymV2K	2022-09-20 08:39:11.988959+00	2022-09-20 08:39:11.988986+00	1	\N	{"tax_rate": 0.54}	f	f
2945	TAX_GROUP	Tax Group	7ZAAQDCQQN	tgRqeA5a9h0W	2022-09-20 08:39:11.989052+00	2022-09-20 08:39:11.98908+00	1	\N	{"tax_rate": 0.18}	f	f
2946	TAX_GROUP	Tax Group	GST: CPT-AU @10.0%	tgrSg9F7Y9sK	2022-09-20 08:39:11.989146+00	2022-09-20 08:39:11.989173+00	1	\N	{"tax_rate": 0.1}	f	f
3080	MERCHANT	Merchant	SPEEDWAY	852	2022-09-20 08:40:15.88943+00	2022-09-20 08:40:15.889465+00	1	\N	\N	f	f
2948	TAX_GROUP	Tax Group	ABN: Ashwin Tax Group @6.0%	tgrVpyLhsOsw	2022-09-20 08:39:11.989334+00	2022-09-20 08:39:11.989361+00	1	\N	{"tax_rate": 0.06}	f	f
2949	TAX_GROUP	Tax Group	MD8XPYK2C6	tgRz68cIQU2p	2022-09-20 08:39:11.98957+00	2022-09-20 08:39:11.98961+00	1	\N	{"tax_rate": 0.18}	f	f
2950	TAX_GROUP	Tax Group	D47UDLB4F8	tgS0DHQJFw70	2022-09-20 08:39:11.989969+00	2022-09-20 08:39:11.990003+00	1	\N	{"tax_rate": 0.18}	f	f
2951	TAX_GROUP	Tax Group	JQUIDWM0VG	tgsaNXWrKCc5	2022-09-20 08:39:11.990078+00	2022-09-20 08:39:11.990106+00	1	\N	{"tax_rate": 0.18}	f	f
680	PROJECT	Project	Project 4	203312	2022-09-20 08:39:06.848723+00	2022-09-20 08:39:06.848753+00	1	t	\N	f	f
2952	TAX_GROUP	Tax Group	CA-PST-ON @0.0%	tgSAZ4hJlF7y	2022-09-20 08:39:11.990171+00	2022-09-20 08:39:11.990198+00	1	\N	{"tax_rate": 0.0}	f	f
2953	TAX_GROUP	Tax Group	MB - GST/RST on Purchases @12.0%	tgSbMd0X3I3O	2022-09-20 08:39:11.990264+00	2022-09-20 08:39:11.99043+00	1	\N	{"tax_rate": 0.12}	f	f
3045	MERCHANT	Merchant	sravan	852	2022-09-20 08:40:15.786308+00	2022-09-20 08:40:15.786337+00	1	\N	\N	f	f
2955	TAX_GROUP	Tax Group	49BVB05MSS	tgsGJxfNb01o	2022-09-20 08:39:11.990605+00	2022-09-20 08:39:11.990632+00	1	\N	{"tax_rate": 0.18}	f	f
2956	TAX_GROUP	Tax Group	1KPDKITYMO	tgSLadNhUC0f	2022-09-20 08:39:11.990698+00	2022-09-20 08:39:11.990726+00	1	\N	{"tax_rate": 0.18}	f	f
2957	TAX_GROUP	Tax Group	H1979NVX85	tgsQFKNzf0SF	2022-09-20 08:39:11.990792+00	2022-09-20 08:39:11.99082+00	1	\N	{"tax_rate": 0.18}	f	f
2958	TAX_GROUP	Tax Group	CDGMCX2GYA	tgsqI5XeBb3m	2022-09-20 08:39:11.990885+00	2022-09-20 08:39:11.990913+00	1	\N	{"tax_rate": 0.18}	f	f
2959	TAX_GROUP	Tax Group	UATHCG2KXH	tgst2mtlstKq	2022-09-20 08:39:11.990979+00	2022-09-20 08:39:11.991006+00	1	\N	{"tax_rate": 0.18}	f	f
2960	TAX_GROUP	Tax Group	D477IUAK5W	tgtaKrDRl8rI	2022-09-20 08:39:11.991072+00	2022-09-20 08:39:11.9911+00	1	\N	{"tax_rate": 0.18}	f	f
2961	TAX_GROUP	Tax Group	OUR0YT9KBK	tgtDlBSNRU91	2022-09-20 08:39:11.991166+00	2022-09-20 08:39:11.991193+00	1	\N	{"tax_rate": 0.18}	f	f
2962	TAX_GROUP	Tax Group	PVDGPPF2SC	tgTekLsroRNM	2022-09-20 08:39:11.99126+00	2022-09-20 08:39:11.991287+00	1	\N	{"tax_rate": 0.18}	f	f
2963	TAX_GROUP	Tax Group	69NR7TNK5P	tgTEr828y2c4	2022-09-20 08:39:11.991353+00	2022-09-20 08:39:11.991501+00	1	\N	{"tax_rate": 0.18}	f	f
2964	TAX_GROUP	Tax Group	A5QP6EJ9HR	tgTmEhiHY9Wb	2022-09-20 08:39:11.991587+00	2022-09-20 08:39:11.991614+00	1	\N	{"tax_rate": 0.18}	f	f
2965	TAX_GROUP	Tax Group	YG9ZHOW03L	tgtnlAuPccmU	2022-09-20 08:39:11.99168+00	2022-09-20 08:39:11.991707+00	1	\N	{"tax_rate": 0.18}	f	f
2966	TAX_GROUP	Tax Group	E2ZA5DOLZP	tgTVkrIoFyPv	2022-09-20 08:39:11.991773+00	2022-09-20 08:39:11.991801+00	1	\N	{"tax_rate": 0.18}	f	f
2967	TAX_GROUP	Tax Group	37YWNDJGXS	tgTz2uOpFEAG	2022-09-20 08:39:11.991866+00	2022-09-20 08:39:11.991893+00	1	\N	{"tax_rate": 0.18}	f	f
2969	TAX_GROUP	Tax Group	CPI-AU @0.0%	tgUcIG8nhjfj	2022-09-20 08:39:11.992052+00	2022-09-20 08:39:11.992079+00	1	\N	{"tax_rate": 0.0}	f	f
2970	TAX_GROUP	Tax Group	N234JZCM07	tguDb9LHWbNf	2022-09-20 08:39:11.992145+00	2022-09-20 08:39:11.992172+00	1	\N	{"tax_rate": 0.18}	f	f
2971	TAX_GROUP	Tax Group	Z8STSQH7B8	tgufmQT6nguV	2022-09-20 08:39:11.992238+00	2022-09-20 08:39:11.992265+00	1	\N	{"tax_rate": 0.18}	f	f
2972	TAX_GROUP	Tax Group	PST: PST_ON_8 @8.0%	tgUHUWIkCUaG	2022-09-20 08:39:11.99233+00	2022-09-20 08:39:11.992496+00	1	\N	{"tax_rate": 0.08}	f	f
2973	TAX_GROUP	Tax Group	OZY0APPOHJ	tguiFXGObZCj	2022-09-20 08:39:11.992577+00	2022-09-20 08:39:11.992604+00	1	\N	{"tax_rate": 0.18}	f	f
2974	TAX_GROUP	Tax Group	tax for twelve @12.5%	tgUL6n1ekT5l	2022-09-20 08:39:11.99267+00	2022-09-20 08:39:11.992697+00	1	\N	{"tax_rate": 0.12}	f	f
2975	TAX_GROUP	Tax Group	AAHWZOY5QZ	tgUMC7ALYxAL	2022-09-20 08:39:11.992763+00	2022-09-20 08:39:11.99279+00	1	\N	{"tax_rate": 0.18}	f	f
2976	TAX_GROUP	Tax Group	MAUZTC2I53	tgUMh6FrCTvo	2022-09-20 08:39:11.992856+00	2022-09-20 08:39:11.992883+00	1	\N	{"tax_rate": 0.18}	f	f
2977	TAX_GROUP	Tax Group	LCT: LCT-AU @25.0%	tgupeKzRMBhH	2022-09-20 08:39:11.992949+00	2022-09-20 08:39:11.992976+00	1	\N	{"tax_rate": 0.25}	f	f
2978	TAX_GROUP	Tax Group	T2PVG1SAHV	tguQQbeTirzC	2022-09-20 08:39:11.993043+00	2022-09-20 08:39:11.99307+00	1	\N	{"tax_rate": 0.18}	f	f
2979	TAX_GROUP	Tax Group	7TF6ZC4WT9	tguu3K3w002b	2022-09-20 08:39:11.993135+00	2022-09-20 08:39:11.993162+00	1	\N	{"tax_rate": 0.18}	f	f
2980	TAX_GROUP	Tax Group	NY - Manhattan @8.5%	tgV1E80ArlhG	2022-09-20 08:39:11.993228+00	2022-09-20 08:39:11.993256+00	1	\N	{"tax_rate": 0.09}	f	f
2981	TAX_GROUP	Tax Group	IZJZZ3S9E7	tgVDrNQDr1Mw	2022-09-20 08:39:11.993321+00	2022-09-20 08:39:11.993359+00	1	\N	{"tax_rate": 0.18}	f	f
2983	TAX_GROUP	Tax Group	GST on capital @10%	tgVlVvok652A	2022-09-20 08:39:11.993655+00	2022-09-20 08:39:11.993682+00	1	\N	{"tax_rate": 0.1}	f	f
2985	TAX_GROUP	Tax Group	VFDBWILTZT	tgVpULIa6cnN	2022-09-20 08:39:11.99384+00	2022-09-20 08:39:11.993868+00	1	\N	{"tax_rate": 0.18}	f	f
2986	TAX_GROUP	Tax Group	OONDUAK3WT	tgVT2VnaV3Kt	2022-09-20 08:39:11.993933+00	2022-09-20 08:39:11.99396+00	1	\N	{"tax_rate": 0.18}	f	f
2987	TAX_GROUP	Tax Group	C72U5RL80N	tgvtS0wCmlx8	2022-09-20 08:39:11.994025+00	2022-09-20 08:39:11.994053+00	1	\N	{"tax_rate": 0.18}	f	f
2988	TAX_GROUP	Tax Group	CA-GST only @0.0%	tgvUMgvIjacH	2022-09-20 08:39:11.994118+00	2022-09-20 08:39:11.994145+00	1	\N	{"tax_rate": 0.0}	f	f
2989	TAX_GROUP	Tax Group	XBBEZH9O4N	tgvXYIFQvNTb	2022-09-20 08:39:11.994211+00	2022-09-20 08:39:11.994239+00	1	\N	{"tax_rate": 0.18}	f	f
2990	TAX_GROUP	Tax Group	SVWPR6H082	tgw8w0rFWK3u	2022-09-20 08:39:11.994305+00	2022-09-20 08:39:11.994332+00	1	\N	{"tax_rate": 0.18}	f	f
2991	TAX_GROUP	Tax Group	SD6IFM5X2M	tgW8w2tofnfF	2022-09-20 08:39:11.994538+00	2022-09-20 08:39:11.994566+00	1	\N	{"tax_rate": 0.18}	f	f
2992	TAX_GROUP	Tax Group	UI777ZUG5P	tgwkRoheKrgP	2022-09-20 08:39:12.003088+00	2022-09-20 08:39:12.003128+00	1	\N	{"tax_rate": 0.18}	f	f
2993	TAX_GROUP	Tax Group	XG2FEN961D	tgWnzNShpJWc	2022-09-20 08:39:12.003197+00	2022-09-20 08:39:12.003225+00	1	\N	{"tax_rate": 0.18}	f	f
2994	TAX_GROUP	Tax Group	ZW806W7J5F	tgWq0Vb4vTKD	2022-09-20 08:39:12.003292+00	2022-09-20 08:39:12.003329+00	1	\N	{"tax_rate": 0.18}	f	f
2995	TAX_GROUP	Tax Group	CABFH8FYWJ	tgWTT4lg0IM2	2022-09-20 08:39:12.003509+00	2022-09-20 08:39:12.003538+00	1	\N	{"tax_rate": 0.18}	f	f
2996	TAX_GROUP	Tax Group	YQKG0LTOUZ	tgwule26Fo6a	2022-09-20 08:39:12.003604+00	2022-09-20 08:39:12.003631+00	1	\N	{"tax_rate": 0.18}	f	f
2997	TAX_GROUP	Tax Group	ABN: Faltu Tax @25.0%	tgWVy7KigBlk	2022-09-20 08:39:12.003698+00	2022-09-20 08:39:12.003726+00	1	\N	{"tax_rate": 0.25}	f	f
2998	TAX_GROUP	Tax Group	5DNCP094R0	tgWW7v553bpm	2022-09-20 08:39:12.003792+00	2022-09-20 08:39:12.00382+00	1	\N	{"tax_rate": 0.18}	f	f
2999	TAX_GROUP	Tax Group	GST: ashwin_tax_code_2 @4.0%	tgwYo6RC8qsA	2022-09-20 08:39:12.003885+00	2022-09-20 08:39:12.003913+00	1	\N	{"tax_rate": 0.04}	f	f
3000	TAX_GROUP	Tax Group	55D90KR22F	tgx09djzUEYt	2022-09-20 08:39:12.003979+00	2022-09-20 08:39:12.004006+00	1	\N	{"tax_rate": 0.18}	f	f
3001	TAX_GROUP	Tax Group	1Q274U30JE	tgX6HYq92Vq3	2022-09-20 08:39:12.004072+00	2022-09-20 08:39:12.0041+00	1	\N	{"tax_rate": 0.18}	f	f
3002	TAX_GROUP	Tax Group	SBNNYXHGJM	tgx7VR8VjhN4	2022-09-20 08:39:12.004165+00	2022-09-20 08:39:12.004193+00	1	\N	{"tax_rate": 0.18}	f	f
3003	TAX_GROUP	Tax Group	0UDWEKF5QQ	tgxCVmcnUcnf	2022-09-20 08:39:12.004258+00	2022-09-20 08:39:12.004286+00	1	\N	{"tax_rate": 0.18}	f	f
3004	TAX_GROUP	Tax Group	OEZ61NIBGN	tgXFxQ9o7ZYt	2022-09-20 08:39:12.004352+00	2022-09-20 08:39:12.004391+00	1	\N	{"tax_rate": 0.18}	f	f
3005	TAX_GROUP	Tax Group	248OHESQX4	tgxlsyzztBiA	2022-09-20 08:39:12.004588+00	2022-09-20 08:39:12.004627+00	1	\N	{"tax_rate": 0.18}	f	f
3006	TAX_GROUP	Tax Group	State: New York State @6.5%	tgXqTTjgvNhW	2022-09-20 08:39:12.004707+00	2022-09-20 08:39:12.004735+00	1	\N	{"tax_rate": 0.07}	f	f
3007	TAX_GROUP	Tax Group	SOYMBT74SM	tgxTtJLTNwML	2022-09-20 08:39:12.004801+00	2022-09-20 08:39:12.004828+00	1	\N	{"tax_rate": 0.18}	f	f
3008	TAX_GROUP	Tax Group	CE1SD2SQIK	tgXu7Tt49YmB	2022-09-20 08:39:12.004894+00	2022-09-20 08:39:12.004921+00	1	\N	{"tax_rate": 0.18}	f	f
3009	TAX_GROUP	Tax Group	GST	tgXueCemFa6Q	2022-09-20 08:39:12.004988+00	2022-09-20 08:39:12.005015+00	1	\N	{"tax_rate": 0.18}	f	f
3010	TAX_GROUP	Tax Group	RGUG2EU1X7	tgXum4KLE0ib	2022-09-20 08:39:12.005081+00	2022-09-20 08:39:12.005108+00	1	\N	{"tax_rate": 0.18}	f	f
3011	TAX_GROUP	Tax Group	XNJ6IYQTT6	tgxVtrVbTvUQ	2022-09-20 08:39:12.005173+00	2022-09-20 08:39:12.0052+00	1	\N	{"tax_rate": 0.18}	f	f
3012	TAX_GROUP	Tax Group	CA-S-AB @0.0%	tgXWjsl5EyeS	2022-09-20 08:39:12.005266+00	2022-09-20 08:39:12.005293+00	1	\N	{"tax_rate": 0.0}	f	f
3013	TAX_GROUP	Tax Group	Pant Tax - 10%	tgy17771Fs0Z	2022-09-20 08:39:12.005461+00	2022-09-20 08:39:12.005482+00	1	\N	{"tax_rate": 0.28}	f	f
3014	TAX_GROUP	Tax Group	AVXYHDXGHR	tgy2bykBE9ad	2022-09-20 08:39:12.005553+00	2022-09-20 08:39:12.005581+00	1	\N	{"tax_rate": 0.18}	f	f
3015	TAX_GROUP	Tax Group	VNISXKB26C	tgY3NmihHRox	2022-09-20 08:39:12.005647+00	2022-09-20 08:39:12.005674+00	1	\N	{"tax_rate": 0.18}	f	f
3016	TAX_GROUP	Tax Group	GWNYCAUI7U	tgY6OZ8p4lMB	2022-09-20 08:39:12.00574+00	2022-09-20 08:39:12.005767+00	1	\N	{"tax_rate": 0.18}	f	f
3017	TAX_GROUP	Tax Group	Z07A9NN1DM	tgy6SBVsh5HM	2022-09-20 08:39:12.005833+00	2022-09-20 08:39:12.00586+00	1	\N	{"tax_rate": 0.18}	f	f
3018	TAX_GROUP	Tax Group	I3LOOW56KF	tgY9sJwvbriq	2022-09-20 08:39:12.005926+00	2022-09-20 08:39:12.005953+00	1	\N	{"tax_rate": 0.18}	f	f
3020	TAX_GROUP	Tax Group	50Q5KYEKC7	tgYdzyKe756m	2022-09-20 08:39:12.006112+00	2022-09-20 08:39:12.006138+00	1	\N	{"tax_rate": 0.18}	f	f
3021	TAX_GROUP	Tax Group	D1IO8OGBJ7	tgYIpi3wxhGt	2022-09-20 08:39:12.006205+00	2022-09-20 08:39:12.006232+00	1	\N	{"tax_rate": 0.18}	f	f
3022	TAX_GROUP	Tax Group	36TEBIWA0N	tgyjcu8nrbTy	2022-09-20 08:39:12.006297+00	2022-09-20 08:39:12.006325+00	1	\N	{"tax_rate": 0.18}	f	f
3023	TAX_GROUP	Tax Group	GST: TS-AU @10.0%	tgYJqx59P3t3	2022-09-20 08:39:12.006525+00	2022-09-20 08:39:12.006546+00	1	\N	{"tax_rate": 0.1}	f	f
3024	TAX_GROUP	Tax Group	SKJX43FH5L	tgyKbeg9FzL2	2022-09-20 08:39:12.006616+00	2022-09-20 08:39:12.006644+00	1	\N	{"tax_rate": 0.18}	f	f
3025	TAX_GROUP	Tax Group	ZIZU1AAHLF	tgYSo7xOCzh7	2022-09-20 08:39:12.00671+00	2022-09-20 08:39:12.006737+00	1	\N	{"tax_rate": 0.18}	f	f
3026	TAX_GROUP	Tax Group	6W2VT8W7SC	tgyvZ3fASuAF	2022-09-20 08:39:12.006803+00	2022-09-20 08:39:12.006831+00	1	\N	{"tax_rate": 0.18}	f	f
3027	TAX_GROUP	Tax Group	Other 2 Sales Tax: GST @18.0%	tgYw6DkCzssM	2022-09-20 08:39:12.006897+00	2022-09-20 08:39:12.006924+00	1	\N	{"tax_rate": 0.18}	f	f
3028	TAX_GROUP	Tax Group	IVX8Q7M4OL	tgYzbD4f1AjL	2022-09-20 08:39:12.00699+00	2022-09-20 08:39:12.007018+00	1	\N	{"tax_rate": 0.18}	f	f
3029	TAX_GROUP	Tax Group	KOY9ZL06FA	tgZ4TqDtyjyq	2022-09-20 08:39:12.007083+00	2022-09-20 08:39:12.007111+00	1	\N	{"tax_rate": 0.18}	f	f
3030	TAX_GROUP	Tax Group	Input tax @0%	tgZCQgT9K0Fk	2022-09-20 08:39:12.007176+00	2022-09-20 08:39:12.007203+00	1	\N	{"tax_rate": 0}	f	f
3031	TAX_GROUP	Tax Group	GHFPC90RHT	tgzDViut4LVz	2022-09-20 08:39:12.007269+00	2022-09-20 08:39:12.007296+00	1	\N	{"tax_rate": 0.18}	f	f
3032	TAX_GROUP	Tax Group	1SBDCCFM3Q	tgzgq9Qnzdvs	2022-09-20 08:39:12.007372+00	2022-09-20 08:39:12.007478+00	1	\N	{"tax_rate": 0.18}	f	f
3033	TAX_GROUP	Tax Group	CUBSMXQ74V	tgZhEaewHZCF	2022-09-20 08:39:12.007542+00	2022-09-20 08:39:12.00758+00	1	\N	{"tax_rate": 0.18}	f	f
3034	TAX_GROUP	Tax Group	QYQKO8SPR6	tgZIde9FACt7	2022-09-20 08:39:12.007646+00	2022-09-20 08:39:12.007674+00	1	\N	{"tax_rate": 0.18}	f	f
3035	TAX_GROUP	Tax Group	3GYAQ1QYHQ	tgZixx6QTCMo	2022-09-20 08:39:12.007739+00	2022-09-20 08:39:12.007767+00	1	\N	{"tax_rate": 0.18}	f	f
3036	TAX_GROUP	Tax Group	L519GF6JU0	tgZjxKuxJfEp	2022-09-20 08:39:12.007832+00	2022-09-20 08:39:12.007859+00	1	\N	{"tax_rate": 0.18}	f	f
3037	TAX_GROUP	Tax Group	0215IGBNYP	tgZJZ7FaRzyy	2022-09-20 08:39:12.007925+00	2022-09-20 08:39:12.007952+00	1	\N	{"tax_rate": 0.18}	f	f
3038	TAX_GROUP	Tax Group	IZZG6UH5Y8	tgzkV4S2Yw1h	2022-09-20 08:39:12.008018+00	2022-09-20 08:39:12.008045+00	1	\N	{"tax_rate": 0.18}	f	f
3039	TAX_GROUP	Tax Group	IKIJX0TM8Y	tgzKVrUU5UNa	2022-09-20 08:39:12.008111+00	2022-09-20 08:39:12.008138+00	1	\N	{"tax_rate": 0.18}	f	f
3040	TAX_GROUP	Tax Group	EGJMQFKSKM	tgzL3ZYEzsoZ	2022-09-20 08:39:12.008203+00	2022-09-20 08:39:12.00823+00	1	\N	{"tax_rate": 0.18}	f	f
3042	TAX_GROUP	Tax Group	Nilesh Tax - 10%	tgzVoKWXqWFB	2022-09-20 08:39:12.015868+00	2022-09-20 08:39:12.015907+00	1	\N	{"tax_rate": 0.28}	f	f
3046	MERCHANT	Merchant	light	852	2022-09-20 08:40:15.786398+00	2022-09-20 08:40:15.786428+00	1	\N	\N	f	f
3047	MERCHANT	Merchant	Abhishek 2	852	2022-09-20 08:40:15.786489+00	2022-09-20 08:40:15.786518+00	1	\N	\N	f	f
3048	MERCHANT	Merchant	Abhishek ji	852	2022-09-20 08:40:15.786579+00	2022-09-20 08:40:15.786608+00	1	\N	\N	f	f
3049	MERCHANT	Merchant	Bob's Burger Joint	852	2022-09-20 08:40:15.786669+00	2022-09-20 08:40:15.786698+00	1	\N	\N	f	f
3050	MERCHANT	Merchant	Books by Bessie	852	2022-09-20 08:40:15.786758+00	2022-09-20 08:40:15.786787+00	1	\N	\N	f	f
3051	MERCHANT	Merchant	Brian Foster	852	2022-09-20 08:40:15.786847+00	2022-09-20 08:40:15.786876+00	1	\N	\N	f	f
3052	MERCHANT	Merchant	Brosnahan Insurance Agency	852	2022-09-20 08:40:15.786937+00	2022-09-20 08:40:15.786966+00	1	\N	\N	f	f
3053	MERCHANT	Merchant	Cal Telephone	852	2022-09-20 08:40:15.787026+00	2022-09-20 08:40:15.787055+00	1	\N	\N	f	f
3054	MERCHANT	Merchant	Chin's Gas and Oil	852	2022-09-20 08:40:15.787115+00	2022-09-20 08:40:15.787144+00	1	\N	\N	f	f
3055	MERCHANT	Merchant	Cigna Health Care	852	2022-09-20 08:40:15.787205+00	2022-09-20 08:40:15.787234+00	1	\N	\N	f	f
3056	MERCHANT	Merchant	Computers by Jenni	852	2022-09-20 08:40:15.787294+00	2022-09-20 08:40:15.787323+00	1	\N	\N	f	f
3057	MERCHANT	Merchant	Credit Card Misc	852	2022-09-20 08:40:15.787384+00	2022-09-20 08:40:15.787413+00	1	\N	\N	f	f
3058	MERCHANT	Merchant	Diego's Road Warrior Bodyshop	852	2022-09-20 08:40:15.787473+00	2022-09-20 08:40:15.787494+00	1	\N	\N	f	f
3059	MERCHANT	Merchant	EDD	852	2022-09-20 08:40:15.787555+00	2022-09-20 08:40:15.794364+00	1	\N	\N	f	f
3060	MERCHANT	Merchant	Ellis Equipment Rental	852	2022-09-20 08:40:15.853096+00	2022-09-20 08:40:15.853163+00	1	\N	\N	f	f
3061	MERCHANT	Merchant	Fidelity	852	2022-09-20 08:40:15.859393+00	2022-09-20 08:40:15.85944+00	1	\N	\N	f	f
3062	MERCHANT	Merchant	Fyle For QBO Paymrnt Sync	852	2022-09-20 08:40:15.859509+00	2022-09-20 08:40:15.859539+00	1	\N	\N	f	f
3063	MERCHANT	Merchant	Hall Properties	852	2022-09-20 08:40:15.859601+00	2022-09-20 08:40:15.85963+00	1	\N	\N	f	f
3064	MERCHANT	Merchant	Hicks Hardware	852	2022-09-20 08:40:15.859691+00	2022-09-20 08:40:15.859721+00	1	\N	\N	f	f
3066	MERCHANT	Merchant	Jessica Lane	852	2022-09-20 08:40:15.859871+00	2022-09-20 08:40:15.8599+00	1	\N	\N	f	f
3067	MERCHANT	Merchant	Justin Glass	852	2022-09-20 08:40:15.859961+00	2022-09-20 08:40:15.85999+00	1	\N	\N	f	f
3068	MERCHANT	Merchant	Lee Advertising	852	2022-09-20 08:40:15.860051+00	2022-09-20 08:40:15.86008+00	1	\N	\N	f	f
3069	MERCHANT	Merchant	Mahoney Mugs	852	2022-09-20 08:40:15.860238+00	2022-09-20 08:40:15.869043+00	1	\N	\N	f	f
3070	MERCHANT	Merchant	Matthew Estrada	852	2022-09-20 08:40:15.869139+00	2022-09-20 08:40:15.881046+00	1	\N	\N	f	f
3071	MERCHANT	Merchant	Met Life Dental	852	2022-09-20 08:40:15.88118+00	2022-09-20 08:40:15.881216+00	1	\N	\N	f	f
3072	MERCHANT	Merchant	Natalie Pope	852	2022-09-20 08:40:15.881292+00	2022-09-20 08:40:15.881324+00	1	\N	\N	f	f
3073	MERCHANT	Merchant	National Eye Care	852	2022-09-20 08:40:15.881394+00	2022-09-20 08:40:15.881424+00	1	\N	\N	f	f
3074	MERCHANT	Merchant	Nilesh Pant	852	2022-09-20 08:40:15.881491+00	2022-09-20 08:40:15.881521+00	1	\N	\N	f	f
3075	MERCHANT	Merchant	Norton Lumber and Building Materials	852	2022-09-20 08:40:15.885902+00	2022-09-20 08:40:15.885941+00	1	\N	\N	f	f
3076	MERCHANT	Merchant	Pam Seitz	852	2022-09-20 08:40:15.888852+00	2022-09-20 08:40:15.888895+00	1	\N	\N	f	f
3077	MERCHANT	Merchant	PG&E	852	2022-09-20 08:40:15.888964+00	2022-09-20 08:40:15.888994+00	1	\N	\N	f	f
3081	MERCHANT	Merchant	Squeaky Kleen Car Wash	852	2022-09-20 08:40:15.889588+00	2022-09-20 08:40:15.924766+00	1	\N	\N	f	f
3082	MERCHANT	Merchant	Sravan	852	2022-09-20 08:40:15.925107+00	2022-09-20 08:40:15.925797+00	1	\N	\N	f	f
3083	MERCHANT	Merchant	Sravan KSK	852	2022-09-20 08:40:15.929249+00	2022-09-20 08:40:15.929334+00	1	\N	\N	f	f
3084	MERCHANT	Merchant	Tania's Nursery	852	2022-09-20 08:40:15.929469+00	2022-09-20 08:40:15.929513+00	1	\N	\N	f	f
3087	MERCHANT	Merchant	Tony Rondonuwu	852	2022-09-20 08:40:15.929905+00	2022-09-20 08:40:15.929935+00	1	\N	\N	f	f
3088	MERCHANT	Merchant	United States Treasury	852	2022-09-20 08:40:15.929995+00	2022-09-20 08:40:15.930123+00	1	\N	\N	f	f
3089	MERCHANT	Merchant	vendor import	852	2022-09-20 08:40:15.930181+00	2022-09-20 08:40:15.930202+00	1	\N	\N	f	f
3090	MERCHANT	Merchant	Alexandra Fitzgerald	852	2022-09-20 08:40:15.930263+00	2022-09-20 08:40:15.930285+00	1	\N	\N	f	f
3091	MERCHANT	Merchant	Allison Hill	852	2022-09-20 08:40:15.930338+00	2022-09-20 08:40:15.930367+00	1	\N	\N	f	f
3092	MERCHANT	Merchant	Amanda Monroe	852	2022-09-20 08:40:15.932232+00	2022-09-20 08:40:15.93226+00	1	\N	\N	f	f
3093	MERCHANT	Merchant	Amazon	852	2022-09-20 08:40:15.96609+00	2022-09-20 08:40:15.966132+00	1	\N	\N	f	f
3094	MERCHANT	Merchant	Amazon Web Services	852	2022-09-20 08:40:15.969507+00	2022-09-20 08:40:15.969554+00	1	\N	\N	f	f
3095	MERCHANT	Merchant	Anna Williamson	852	2022-09-20 08:40:15.969624+00	2022-09-20 08:40:15.969653+00	1	\N	\N	f	f
3096	MERCHANT	Merchant	Anne Glass	852	2022-09-20 08:40:15.969714+00	2022-09-20 08:40:15.969743+00	1	\N	\N	f	f
3097	MERCHANT	Merchant	Anne Jackson	852	2022-09-20 08:40:15.969803+00	2022-09-20 08:40:15.969831+00	1	\N	\N	f	f
3102	MERCHANT	Merchant	Brenda Hawkins	852	2022-09-20 08:40:15.970353+00	2022-09-20 08:40:15.970382+00	1	\N	\N	f	f
3103	MERCHANT	Merchant	Central Coalfields	852	2022-09-20 08:40:15.970441+00	2022-09-20 08:40:15.97047+00	1	\N	\N	f	f
3104	MERCHANT	Merchant	Chris Curtis	852	2022-09-20 08:40:15.970531+00	2022-09-20 08:40:15.970559+00	1	\N	\N	f	f
3105	MERCHANT	Merchant	Debit Card Misc	852	2022-09-20 08:40:15.97062+00	2022-09-20 08:40:15.970649+00	1	\N	\N	f	f
3106	MERCHANT	Merchant	Dominos	852	2022-09-20 08:40:15.970709+00	2022-09-20 08:40:15.970738+00	1	\N	\N	f	f
3107	MERCHANT	Merchant	DOMINO'S	852	2022-09-20 08:40:15.970798+00	2022-09-20 08:40:15.970827+00	1	\N	\N	f	f
3108	MERCHANT	Merchant	DOMINO'S P	852	2022-09-20 08:40:15.970887+00	2022-09-20 08:40:15.970916+00	1	\N	\N	f	f
3109	MERCHANT	Merchant	Edward Blankenship	852	2022-09-20 08:40:15.970976+00	2022-09-20 08:40:15.971005+00	1	\N	\N	f	f
3110	MERCHANT	Merchant	Fyle Vendor	852	2022-09-20 08:40:15.971065+00	2022-09-20 08:40:15.971094+00	1	\N	\N	f	f
3111	MERCHANT	Merchant	Gokul	852	2022-09-20 08:40:15.971251+00	2022-09-20 08:40:15.971281+00	1	\N	\N	f	f
3112	MERCHANT	Merchant	Gokul Kathiresan	852	2022-09-20 08:40:15.971343+00	2022-09-20 08:40:15.971372+00	1	\N	\N	f	f
3113	MERCHANT	Merchant	Gokul Kathiresan King	852	2022-09-20 08:40:15.971433+00	2022-09-20 08:40:15.971462+00	1	\N	\N	f	f
3114	MERCHANT	Merchant	Jonathan Elliott	852	2022-09-20 08:40:15.971523+00	2022-09-20 08:40:15.971552+00	1	\N	\N	f	f
3115	MERCHANT	Merchant	Joshua Wood	852	2022-09-20 08:40:15.971612+00	2022-09-20 08:40:15.971642+00	1	\N	\N	f	f
3116	MERCHANT	Merchant	Lord Voldemort	852	2022-09-20 08:40:15.971702+00	2022-09-20 08:40:15.972321+00	1	\N	\N	f	f
3117	MERCHANT	Merchant	Matt Damon	852	2022-09-20 08:40:15.972502+00	2022-09-20 08:40:15.972548+00	1	\N	\N	f	f
3118	MERCHANT	Merchant	Peter Derek	852	2022-09-20 08:40:15.972641+00	2022-09-20 08:40:15.972675+00	1	\N	\N	f	f
3119	MERCHANT	Merchant	Ravindra Jadeja	852	2022-09-20 08:40:15.972755+00	2022-09-20 08:40:15.972783+00	1	\N	\N	f	f
3120	MERCHANT	Merchant	Ryan Gallagher	852	2022-09-20 08:40:15.972877+00	2022-09-20 08:40:15.972922+00	1	\N	\N	f	f
3121	MERCHANT	Merchant	Shwetabh Ji	852	2022-09-20 08:40:15.987609+00	2022-09-20 08:40:15.987662+00	1	\N	\N	f	f
3122	MERCHANT	Merchant	staging vendor	852	2022-09-20 08:40:15.987754+00	2022-09-20 08:40:15.987785+00	1	\N	\N	f	f
3123	MERCHANT	Merchant	STEAK-N-SHAKE#0664	852	2022-09-20 08:40:15.987861+00	2022-09-20 08:40:15.987898+00	1	\N	\N	f	f
3124	MERCHANT	Merchant	Theresa Brown	852	2022-09-20 08:40:15.987962+00	2022-09-20 08:40:15.992213+00	1	\N	\N	f	f
3125	MERCHANT	Merchant	Uber	852	2022-09-20 08:40:15.992369+00	2022-09-20 08:40:15.992416+00	1	\N	\N	f	f
3126	MERCHANT	Merchant	Victor Martinez	852	2022-09-20 08:40:15.99252+00	2022-09-20 08:40:15.992565+00	1	\N	\N	f	f
3127	MERCHANT	Merchant	Victor Martinez II	852	2022-09-20 08:40:15.992712+00	2022-09-20 08:40:15.992763+00	1	\N	\N	f	f
3129	MERCHANT	Merchant	final staging vandor	852	2022-09-20 08:40:15.993665+00	2022-09-20 08:40:15.993716+00	1	\N	\N	f	f
3130	MERCHANT	Merchant	Killua	852	2022-09-20 08:40:15.993791+00	2022-09-20 08:40:15.993822+00	1	\N	\N	f	f
3131	MERCHANT	Merchant	labhvam	852	2022-09-20 08:40:15.993884+00	2022-09-20 08:40:15.993914+00	1	\N	\N	f	f
3132	MERCHANT	Merchant	Fyle new employeeee	852	2022-09-20 08:40:16.008963+00	2022-09-20 08:40:16.009024+00	1	\N	\N	f	f
3133	MERCHANT	Merchant	Ashwin Vendor 2.0	852	2022-09-20 08:40:16.009604+00	2022-09-20 08:40:16.009724+00	1	\N	\N	f	f
3134	MERCHANT	Merchant	California EDD (HQ)	852	2022-09-20 08:40:16.010008+00	2022-09-20 08:40:16.010116+00	1	\N	\N	f	f
3135	MERCHANT	Merchant	CPR ATLANTIC CASPER	852	2022-09-20 08:40:16.010378+00	2022-09-20 08:40:16.010643+00	1	\N	\N	f	f
3136	MERCHANT	Merchant	EXPENSIFY.COM SAN FRANCISCO USA	852	2022-09-20 08:40:16.0108+00	2022-09-20 08:40:16.010851+00	1	\N	\N	f	f
3137	MERCHANT	Merchant	FACEBK RUW7LCPQU2	852	2022-09-20 08:40:16.010972+00	2022-09-20 08:40:16.011019+00	1	\N	\N	f	f
3138	MERCHANT	Merchant	FORT DODGE FLIGHT SUPP	852	2022-09-20 08:40:16.011129+00	2022-09-20 08:40:16.011169+00	1	\N	\N	f	f
3139	MERCHANT	Merchant	GOOGLE*GOOGLE STORAGE IRELAND IRL	852	2022-09-20 08:40:16.011277+00	2022-09-20 08:40:16.011317+00	1	\N	\N	f	f
3140	MERCHANT	Merchant	GRAND AIRE, INC.	852	2022-09-20 08:40:16.011418+00	2022-09-20 08:40:16.011458+00	1	\N	\N	f	f
3141	MERCHANT	Merchant	Internal Revenue Service-FUTA (HQ)	852	2022-09-20 08:40:16.011558+00	2022-09-20 08:40:16.011598+00	1	\N	\N	f	f
3142	MERCHANT	Merchant	Internal Revenue Service- Income,FICA (HQ)	852	2022-09-20 08:40:16.011692+00	2022-09-20 08:40:16.011732+00	1	\N	\N	f	f
3143	MERCHANT	Merchant	MAILCHIMP ATLANTA USA	852	2022-09-20 08:40:16.050336+00	2022-09-20 08:40:16.050387+00	1	\N	\N	f	f
3144	MERCHANT	Merchant	MARRIOTT ANCHORAGE	852	2022-09-20 08:40:16.050468+00	2022-09-20 08:40:16.0505+00	1	\N	\N	f	f
3145	MERCHANT	Merchant	New York City (HQ)	852	2022-09-20 08:40:16.050571+00	2022-09-20 08:40:16.050601+00	1	\N	\N	f	f
3146	MERCHANT	Merchant	New York County (HQ)	852	2022-09-20 08:40:16.050668+00	2022-09-20 08:40:16.050697+00	1	\N	\N	f	f
3147	MERCHANT	Merchant	New York State (HQ)	852	2022-09-20 08:40:16.05076+00	2022-09-20 08:40:16.05079+00	1	\N	\N	f	f
3148	MERCHANT	Merchant	Nilesh	852	2022-09-20 08:40:16.050853+00	2022-09-20 08:40:16.050882+00	1	\N	\N	f	f
3149	MERCHANT	Merchant	Nippoin Accountants	852	2022-09-20 08:40:16.050945+00	2022-09-20 08:40:16.050967+00	1	\N	\N	f	f
3150	MERCHANT	Merchant	Purchase Al Dept Of Revenue	852	2022-09-20 08:40:16.05101+00	2022-09-20 08:40:16.051021+00	1	\N	\N	f	f
3151	MERCHANT	Merchant	Purchase Marshall Tag 2562754042	852	2022-09-20 08:40:16.051072+00	2022-09-20 08:40:16.051101+00	1	\N	\N	f	f
3152	MERCHANT	Merchant	Purchase Taxhandlingfee2562754042	852	2022-09-20 08:40:16.051163+00	2022-09-20 08:40:16.051192+00	1	\N	\N	f	f
3153	MERCHANT	Merchant	State Board of Equalization (HQ)	852	2022-09-20 08:40:16.052635+00	2022-09-20 08:40:16.052694+00	1	\N	\N	f	f
3154	MERCHANT	Merchant	Stein Investments (HQ)	852	2022-09-20 08:40:16.052799+00	2022-09-20 08:40:16.053056+00	1	\N	\N	f	f
3155	MERCHANT	Merchant	Store Tax Agency (HQ)	852	2022-09-20 08:40:16.053126+00	2022-09-20 08:40:16.053155+00	1	\N	\N	f	f
3156	MERCHANT	Merchant	Swiggy	852	2022-09-20 08:40:16.053216+00	2022-09-20 08:40:16.053245+00	1	\N	\N	f	f
3157	MERCHANT	Merchant	Tax Agency AK (3 - Honeycomb Holdings Inc.) (20210317-104301)	852	2022-09-20 08:40:16.053306+00	2022-09-20 08:40:16.053336+00	1	\N	\N	f	f
3158	MERCHANT	Merchant	Test Vendor	852	2022-09-20 08:40:16.053396+00	2022-09-20 08:40:16.053425+00	1	\N	\N	f	f
3159	MERCHANT	Merchant	TOWNEPLACE SUITES BY M	852	2022-09-20 08:40:16.053486+00	2022-09-20 08:40:16.053515+00	1	\N	\N	f	f
3160	MERCHANT	Merchant	ezagpulmvbxgogg	852	2022-09-20 08:40:16.053575+00	2022-09-20 08:40:16.053604+00	1	\N	\N	f	f
3161	MERCHANT	Merchant	hxnvqlydmnudjpi	852	2022-09-20 08:40:16.053664+00	2022-09-20 08:40:16.053693+00	1	\N	\N	f	f
3162	MERCHANT	Merchant	Joanna	852	2022-09-20 08:40:16.053753+00	2022-09-20 08:40:16.053782+00	1	\N	\N	f	f
3163	MERCHANT	Merchant	Provincial Treasurer AB	852	2022-09-20 08:40:16.053842+00	2022-09-20 08:40:16.053872+00	1	\N	\N	f	f
3164	MERCHANT	Merchant	Receiver General	852	2022-09-20 08:40:16.053924+00	2022-09-20 08:40:16.053945+00	1	\N	\N	f	f
3165	MERCHANT	Merchant	ADP	852	2022-09-20 08:40:24.027869+00	2022-09-20 08:40:24.027911+00	1	\N	\N	f	f
3166	MERCHANT	Merchant	Advisor Printing	852	2022-09-20 08:40:24.02797+00	2022-09-20 08:40:24.027998+00	1	\N	\N	f	f
3167	MERCHANT	Merchant	akavuluru	852	2022-09-20 08:40:24.028055+00	2022-09-20 08:40:24.028083+00	1	\N	\N	f	f
3168	MERCHANT	Merchant	American Express	852	2022-09-20 08:40:24.02827+00	2022-09-20 08:40:24.028309+00	1	\N	\N	f	f
3169	MERCHANT	Merchant	Boardwalk Post	852	2022-09-20 08:40:24.028366+00	2022-09-20 08:40:24.028393+00	1	\N	\N	f	f
3170	MERCHANT	Merchant	Canyon CPA	852	2022-09-20 08:40:24.028449+00	2022-09-20 08:40:24.028476+00	1	\N	\N	f	f
3171	MERCHANT	Merchant	Citi Bank	852	2022-09-20 08:40:24.028532+00	2022-09-20 08:40:24.02856+00	1	\N	\N	f	f
3172	MERCHANT	Merchant	Consulting Grid	852	2022-09-20 08:40:24.028616+00	2022-09-20 08:40:24.028643+00	1	\N	\N	f	f
3173	MERCHANT	Merchant	Cornerstone	852	2022-09-20 08:40:24.028699+00	2022-09-20 08:40:24.028726+00	1	\N	\N	f	f
3174	MERCHANT	Merchant	Entity V100	852	2022-09-20 08:40:24.028783+00	2022-09-20 08:40:24.02881+00	1	\N	\N	f	f
3175	MERCHANT	Merchant	Entity V200	852	2022-09-20 08:40:24.028874+00	2022-09-20 08:40:24.028901+00	1	\N	\N	f	f
3176	MERCHANT	Merchant	Entity V300	852	2022-09-20 08:40:24.028958+00	2022-09-20 08:40:24.028985+00	1	\N	\N	f	f
3177	MERCHANT	Merchant	Entity V400	852	2022-09-20 08:40:24.029041+00	2022-09-20 08:40:24.029068+00	1	\N	\N	f	f
3181	MERCHANT	Merchant	Global Printing	852	2022-09-20 08:40:24.029507+00	2022-09-20 08:40:24.029534+00	1	\N	\N	f	f
3182	MERCHANT	Merchant	Global Properties Inc.	852	2022-09-20 08:40:24.029591+00	2022-09-20 08:40:24.029618+00	1	\N	\N	f	f
3183	MERCHANT	Merchant	gokul	852	2022-09-20 08:40:24.029675+00	2022-09-20 08:40:24.029702+00	1	\N	\N	f	f
3184	MERCHANT	Merchant	Green Team Waste Management	852	2022-09-20 08:40:24.029758+00	2022-09-20 08:40:24.029785+00	1	\N	\N	f	f
3185	MERCHANT	Merchant	Hanson Learning Solutions	852	2022-09-20 08:40:24.029841+00	2022-09-20 08:40:24.029868+00	1	\N	\N	f	f
3186	MERCHANT	Merchant	HC Equipment Repair	852	2022-09-20 08:40:24.029925+00	2022-09-20 08:40:24.029952+00	1	\N	\N	f	f
3187	MERCHANT	Merchant	Investor CPA	852	2022-09-20 08:40:24.030009+00	2022-09-20 08:40:24.030036+00	1	\N	\N	f	f
3188	MERCHANT	Merchant	Kaufman & Langer LLP	852	2022-09-20 08:40:24.030093+00	2022-09-20 08:40:24.030131+00	1	\N	\N	f	f
3189	MERCHANT	Merchant	Kristofferson Consulting	852	2022-09-20 08:40:24.030308+00	2022-09-20 08:40:24.030336+00	1	\N	\N	f	f
3190	MERCHANT	Merchant	Lee Thomas	852	2022-09-20 08:40:24.030392+00	2022-09-20 08:40:24.030425+00	1	\N	\N	f	f
3191	MERCHANT	Merchant	Lenovo	852	2022-09-20 08:40:24.030482+00	2022-09-20 08:40:24.030509+00	1	\N	\N	f	f
3192	MERCHANT	Merchant	Linda Hicks	852	2022-09-20 08:40:24.030566+00	2022-09-20 08:40:24.030593+00	1	\N	\N	f	f
3193	MERCHANT	Merchant	Magnolia CPA	852	2022-09-20 08:40:24.030649+00	2022-09-20 08:40:24.030677+00	1	\N	\N	f	f
3194	MERCHANT	Merchant	Massachusetts Department of Revenue	852	2022-09-20 08:40:24.030733+00	2022-09-20 08:40:24.03076+00	1	\N	\N	f	f
3195	MERCHANT	Merchant	Microns Consulting	852	2022-09-20 08:40:24.030816+00	2022-09-20 08:40:24.030844+00	1	\N	\N	f	f
3196	MERCHANT	Merchant	National Grid	852	2022-09-20 08:40:24.0309+00	2022-09-20 08:40:24.030927+00	1	\N	\N	f	f
3197	MERCHANT	Merchant	National Insurance	852	2022-09-20 08:40:24.030989+00	2022-09-20 08:40:24.031017+00	1	\N	\N	f	f
3198	MERCHANT	Merchant	Neighborhood Printers	852	2022-09-20 08:40:24.031073+00	2022-09-20 08:40:24.031101+00	1	\N	\N	f	f
3199	MERCHANT	Merchant	Nilesh, Dhoni	852	2022-09-20 08:40:24.031264+00	2022-09-20 08:40:24.031289+00	1	\N	\N	f	f
3200	MERCHANT	Merchant	Paramount Consulting	852	2022-09-20 08:40:24.031343+00	2022-09-20 08:40:24.031356+00	1	\N	\N	f	f
3201	MERCHANT	Merchant	Prima Printing	852	2022-09-20 08:40:24.031395+00	2022-09-20 08:40:24.031415+00	1	\N	\N	f	f
3202	MERCHANT	Merchant	Prosper Post	852	2022-09-20 08:40:24.031483+00	2022-09-20 08:40:24.03151+00	1	\N	\N	f	f
3203	MERCHANT	Merchant	Quali Consultants	852	2022-09-20 08:40:24.031566+00	2022-09-20 08:40:24.031593+00	1	\N	\N	f	f
3204	MERCHANT	Merchant	Quick Post	852	2022-09-20 08:40:24.03165+00	2022-09-20 08:40:24.031677+00	1	\N	\N	f	f
3205	MERCHANT	Merchant	River Glen Insurance	852	2022-09-20 08:40:24.031733+00	2022-09-20 08:40:24.03176+00	1	\N	\N	f	f
3206	MERCHANT	Merchant	Sachin, Saran	852	2022-09-20 08:40:24.031828+00	2022-09-20 08:40:24.031856+00	1	\N	\N	f	f
3207	MERCHANT	Merchant	Scribe Post	852	2022-09-20 08:40:24.031917+00	2022-09-20 08:40:24.031944+00	1	\N	\N	f	f
3208	MERCHANT	Merchant	Singleton Brothers CPA	852	2022-09-20 08:40:24.032001+00	2022-09-20 08:40:24.032028+00	1	\N	\N	f	f
3209	MERCHANT	Merchant	Srav	852	2022-09-20 08:40:24.032084+00	2022-09-20 08:40:24.032123+00	1	\N	\N	f	f
3210	MERCHANT	Merchant	State Bank	852	2022-09-20 08:40:24.03227+00	2022-09-20 08:40:24.032298+00	1	\N	\N	f	f
3211	MERCHANT	Merchant	The Nonprofit Alliance	852	2022-09-20 08:40:24.032354+00	2022-09-20 08:40:24.032382+00	1	\N	\N	f	f
3212	MERCHANT	Merchant	The Post Company	852	2022-09-20 08:40:24.032511+00	2022-09-20 08:40:24.032678+00	1	\N	\N	f	f
3213	MERCHANT	Merchant	Vaishnavi Primary	852	2022-09-20 08:40:24.032979+00	2022-09-20 08:40:24.033121+00	1	\N	\N	f	f
3214	MERCHANT	Merchant	Vision Post	852	2022-09-20 08:40:24.033563+00	2022-09-20 08:40:24.033617+00	1	\N	\N	f	f
3215	MERCHANT	Merchant	VM	852	2022-09-20 08:40:24.040086+00	2022-09-20 08:40:24.040137+00	1	\N	\N	f	f
3216	MERCHANT	Merchant	Worldwide Commercial	852	2022-09-20 08:40:24.040336+00	2022-09-20 08:40:24.040364+00	1	\N	\N	f	f
3217	MERCHANT	Merchant	Yash	852	2022-09-20 08:40:24.040432+00	2022-09-20 08:40:24.040477+00	1	\N	\N	f	f
1	EMPLOYEE	Employee	ashwin.t@fyle.in	ouVLOYP8lelN	2022-09-20 08:39:02.390021+00	2022-09-20 08:39:02.390094+00	1	\N	{"user_id": "usqywo0f3nBY", "location": null, "full_name": "Joanna", "department": null, "department_id": null, "employee_code": null, "department_code": null}	t	f
3222	TAX_GROUP	Tax Group	N27HHEOEY8	tgA7LDFGfctm	2022-09-28 11:20:40.693894+00	2022-09-28 11:20:40.693975+00	1	\N	{"tax_rate": 0.18}	f	f
3223	TAX_GROUP	Tax Group	H7FH7Q9WJ6	tghvvY536lD4	2022-09-28 11:20:40.694094+00	2022-09-28 11:20:40.694113+00	1	\N	{"tax_rate": 0.18}	f	f
3224	TAX_GROUP	Tax Group	FML12E68S6	tgYjjc9hfkNP	2022-09-28 11:20:40.694203+00	2022-09-28 11:20:40.694237+00	1	\N	{"tax_rate": 0.18}	f	f
2692	TAX_GROUP	Tax Group	EC Purchase Goods Standard Rate Input	tg03sPKjNkKq	2022-09-20 08:39:11.565395+00	2022-09-20 08:39:11.565464+00	1	\N	{"tax_rate": 0.2}	t	f
2720	TAX_GROUP	Tax Group	UK Purchase Goods Reduced Rate	tg51CNoNSxiO	2022-09-20 08:39:11.582902+00	2022-09-20 08:39:11.582963+00	1	\N	{"tax_rate": 0.05}	t	f
2725	TAX_GROUP	Tax Group	EC Purchase Services Reduced Rate Input	tg6icu6uquJZ	2022-09-20 08:39:11.583955+00	2022-09-20 08:39:11.584005+00	1	\N	{"tax_rate": 0.05}	t	f
2737	TAX_GROUP	Tax Group	UK Import Goods Standard Rate	tg7sE7ZSw5Yn	2022-09-20 08:39:11.592389+00	2022-09-20 08:39:11.592419+00	1	\N	{"tax_rate": 0.2}	t	f
2751	TAX_GROUP	Tax Group	Other Output Tax Adjustments	tga9OiFNWcDh	2022-09-20 08:39:11.632416+00	2022-09-20 08:39:11.632436+00	1	\N	{"tax_rate": 1.0}	t	f
2822	TAX_GROUP	Tax Group	Standard Rate (Capital Goods) Input	tgGn1oIv0odS	2022-09-20 08:39:11.65591+00	2022-09-20 08:39:11.655941+00	1	\N	{"tax_rate": 0.15}	t	f
2834	TAX_GROUP	Tax Group	G13 Purchases for Input Tax Sales	tghyBGpukx04	2022-09-20 08:39:11.657436+00	2022-09-20 08:39:11.657456+00	1	\N	{"tax_rate": 0.1}	t	f
2840	TAX_GROUP	Tax Group	G15 Capital Purchases for Private Use	tginkDefSKP7	2022-09-20 08:39:11.658091+00	2022-09-20 08:39:11.658111+00	1	\N	{"tax_rate": 0.1}	t	f
2857	TAX_GROUP	Tax Group	Standard Rate Input	tgkrTg3hsBGo	2022-09-20 08:39:11.674255+00	2022-09-20 08:39:11.674277+00	1	\N	{"tax_rate": 0.15}	t	f
2869	TAX_GROUP	Tax Group	G10 Capital Acquisition	tgLj0KdoNp6n	2022-09-20 08:39:11.676154+00	2022-09-20 08:39:11.676176+00	1	\N	{"tax_rate": 0.1}	t	f
103	CATEGORY	Category	kfliuyfdlify liuflif	184629	2022-09-20 08:39:03.37353+00	2022-09-20 08:39:03.373552+00	1	t	\N	f	f
106	CATEGORY	Category	Miscellaneous	163671	2022-09-20 08:39:03.374511+00	2022-09-20 08:39:03.374531+00	1	t	\N	f	f
2873	TAX_GROUP	Tax Group	UK Purchase in Reverse Charge Box 6 Reduced Rate UK Input	tgLq1ZgwHe2N	2022-09-20 08:39:11.676895+00	2022-09-20 08:39:11.676915+00	1	\N	{"tax_rate": 0.05}	t	f
2875	TAX_GROUP	Tax Group	G13 Capital Purchases for Input Tax Sales	tgm1nnhMeKs4	2022-09-20 08:39:11.677165+00	2022-09-20 08:39:11.677204+00	1	\N	{"tax_rate": 0.1}	t	f
2884	TAX_GROUP	Tax Group	EC Purchase Goods Reduced Rate Input	tgMYde7GlsXF	2022-09-20 08:39:11.67889+00	2022-09-20 08:39:11.678912+00	1	\N	{"tax_rate": 0.05}	t	f
2893	TAX_GROUP	Tax Group	UK Purchase Reverse Charge Standard Rate Input	tgNqkGml9EGM	2022-09-20 08:39:11.972991+00	2022-09-20 08:39:11.973059+00	1	\N	{"tax_rate": 0.2}	t	f
2905	TAX_GROUP	Tax Group	UK Import Services Reduced Rate	tgOULxUfH6EV	2022-09-20 08:39:11.975849+00	2022-09-20 08:39:11.975876+00	1	\N	{"tax_rate": 0.05}	t	f
2916	TAX_GROUP	Tax Group	UK Purchase Goods Standard Rate	tgPM90wg21fN	2022-09-20 08:39:11.977108+00	2022-09-20 08:39:11.977135+00	1	\N	{"tax_rate": 0.2}	t	f
2922	TAX_GROUP	Tax Group	G11 Other Acquisition	tgPzaJl9YEIy	2022-09-20 08:39:11.977813+00	2022-09-20 08:39:11.97784+00	1	\N	{"tax_rate": 0.1}	t	f
2939	TAX_GROUP	Tax Group	Change in Use Input	tgRi0weoxcIg	2022-09-20 08:39:11.981003+00	2022-09-20 08:39:11.981102+00	1	\N	{"tax_rate": 0.15}	t	f
2947	TAX_GROUP	Tax Group	UK Import Services Standard Rate	tgRuU4aJDtp0	2022-09-20 08:39:11.98924+00	2022-09-20 08:39:11.989267+00	1	\N	{"tax_rate": 0.2}	t	f
2954	TAX_GROUP	Tax Group	G15 Purchases for Private Use	tgsFw1s5tPre	2022-09-20 08:39:11.990512+00	2022-09-20 08:39:11.99054+00	1	\N	{"tax_rate": 0.1}	t	f
2968	TAX_GROUP	Tax Group	EC Purchase Services Standard Rate Input	tgU4rY4PFZpv	2022-09-20 08:39:11.991959+00	2022-09-20 08:39:11.991986+00	1	\N	{"tax_rate": 0.2}	t	f
2982	TAX_GROUP	Tax Group	UK Purchase Reverse Charge Reduced Rate Input	tgVKGWKL7pPt	2022-09-20 08:39:11.993562+00	2022-09-20 08:39:11.99359+00	1	\N	{"tax_rate": 0.05}	t	f
2984	TAX_GROUP	Tax Group	UK Import Goods Reduced Rate	tgVnRMSNQpKK	2022-09-20 08:39:11.993748+00	2022-09-20 08:39:11.993775+00	1	\N	{"tax_rate": 0.05}	t	f
3019	TAX_GROUP	Tax Group	UK Purchase in Reverse Charge Box 6 Standard Rate UK Input	tgYDec7KVOw4	2022-09-20 08:39:12.006019+00	2022-09-20 08:39:12.006046+00	1	\N	{"tax_rate": 0.2}	t	f
3041	TAX_GROUP	Tax Group	G10 Motor Vehicle Acquisition	tgZUh8neIfxC	2022-09-20 08:39:12.008296+00	2022-09-20 08:39:12.008323+00	1	\N	{"tax_rate": 0.1}	t	f
3248	TAX_GROUP	Tax Group	No Input VAT	tgUIrIce3bbR	2022-09-29 12:09:34.570694+00	2022-09-29 12:09:34.570723+00	1	\N	{"tax_rate": 0.0}	t	f
3228	TAX_GROUP	Tax Group	G15 GST Free Purchases for Private Use	tg1mbgnpCD74	2022-09-29 12:09:34.562145+00	2022-09-29 12:09:34.562208+00	1	\N	{"tax_rate": 0.0}	t	f
3229	TAX_GROUP	Tax Group	1F Luxury Car Tax Refundable	tg2vcq1pLm4T	2022-09-29 12:09:34.562296+00	2022-09-29 12:09:34.562326+00	1	\N	{"tax_rate": 0.0}	t	f
3230	TAX_GROUP	Tax Group	EC Purchase Goods Exempt Rate	tgAJLZUDLsNQ	2022-09-29 12:09:34.562396+00	2022-09-29 12:09:34.562425+00	1	\N	{"tax_rate": 0.0}	t	f
3232	TAX_GROUP	Tax Group	G13 GST Free Capital Purchases for Input Tax Sales	tgbMrQbQlYQy	2022-09-29 12:09:34.562592+00	2022-09-29 12:09:34.562622+00	1	\N	{"tax_rate": 0.0}	t	f
3233	TAX_GROUP	Tax Group	1D Wine Equalisation Tax Refundable	tgcn2gXFEHY7	2022-09-29 12:09:34.562691+00	2022-09-29 12:09:34.562721+00	1	\N	{"tax_rate": 0.0}	t	f
270	CATEGORY	Category	Automobile	135717	2022-09-20 08:39:05.193039+00	2022-09-20 08:39:05.193068+00	1	t	\N	f	f
3234	TAX_GROUP	Tax Group	G13 GST Free Purchases for Input Tax Sales	tgdoF2v8wmrE	2022-09-29 12:09:34.562789+00	2022-09-29 12:09:34.562818+00	1	\N	{"tax_rate": 0.0}	t	f
3235	TAX_GROUP	Tax Group	G14 GST Free Non-Capital Purchases	tgemain9bLa7	2022-09-29 12:09:34.562886+00	2022-09-29 12:09:34.562915+00	1	\N	{"tax_rate": 0.0}	t	f
3236	TAX_GROUP	Tax Group	Other Goods Imported (Not Capital Goods)	tgkxSRv2TaRu	2022-09-29 12:09:34.569172+00	2022-09-29 12:09:34.569223+00	1	\N	{"tax_rate": 0.0}	t	f
3237	TAX_GROUP	Tax Group	G14 GST Free Capital Purchases	tgl1DZ4CwRD4	2022-09-29 12:09:34.569334+00	2022-09-29 12:09:34.569364+00	1	\N	{"tax_rate": 0.0}	t	f
45	CATEGORY	Category	General Expenses	135996	2022-09-20 08:39:03.256232+00	2022-09-20 08:39:03.256319+00	1	t	\N	f	f
3238	TAX_GROUP	Tax Group	UK Import Goods Exempt Rate	tgMiYO0TshL4	2022-09-29 12:09:34.569436+00	2022-09-29 12:09:34.569465+00	1	\N	{"tax_rate": 0.0}	t	f
3239	TAX_GROUP	Tax Group	UK Purchase Services Exempt Rate	tgmL0gaIk8QA	2022-09-29 12:09:34.569535+00	2022-09-29 12:09:34.569575+00	1	\N	{"tax_rate": 0.0}	t	f
3240	TAX_GROUP	Tax Group	UK Purchase in Reverse Charge Box 6 Zero Rate UK	tgoP36Onf0Zk	2022-09-29 12:09:34.569787+00	2022-09-29 12:09:34.569824+00	1	\N	{"tax_rate": 0.0}	t	f
3241	TAX_GROUP	Tax Group	G15 GST Free Capital Purchases for Private Use	tgq53BJYGByc	2022-09-29 12:09:34.569901+00	2022-09-29 12:09:34.569931+00	1	\N	{"tax_rate": 0.0}	t	f
3242	TAX_GROUP	Tax Group	UK Import Services Zero Rate	tgQgmFdOAuCf	2022-09-29 12:09:34.5701+00	2022-09-29 12:09:34.57013+00	1	\N	{"tax_rate": 0.0}	t	f
3243	TAX_GROUP	Tax Group	UK Purchase Goods Exempt Rate	tgQXbB0B4ayf	2022-09-29 12:09:34.5702+00	2022-09-29 12:09:34.570229+00	1	\N	{"tax_rate": 0.0}	t	f
3245	TAX_GROUP	Tax Group	UK Purchase in Reverse Charge Box 6 Exempt UK	tgS7uGNdnU3G	2022-09-29 12:09:34.570397+00	2022-09-29 12:09:34.570427+00	1	\N	{"tax_rate": 0.0}	t	f
3246	TAX_GROUP	Tax Group	Capital Goods Imported	tgtJswuKZ0Tm	2022-09-29 12:09:34.570497+00	2022-09-29 12:09:34.570526+00	1	\N	{"tax_rate": 0.0}	t	f
3247	TAX_GROUP	Tax Group	UK Import Goods Zero Rate	tgU9adO9cZ0v	2022-09-29 12:09:34.570596+00	2022-09-29 12:09:34.570625+00	1	\N	{"tax_rate": 0.0}	t	f
3249	TAX_GROUP	Tax Group	UK Purchase Goods Zero Rate	tgUMN1LbRgQn	2022-09-29 12:09:34.570792+00	2022-09-29 12:09:34.570821+00	1	\N	{"tax_rate": 0.0}	t	f
3250	TAX_GROUP	Tax Group	EC Purchase Services Zero Rate	tgv3qq4c4SkN	2022-09-29 12:09:34.57089+00	2022-09-29 12:09:34.57092+00	1	\N	{"tax_rate": 0.0}	t	f
3251	TAX_GROUP	Tax Group	G18 Input Tax Credit Adjustment	tgVdyPpozeoS	2022-09-29 12:09:34.571078+00	2022-09-29 12:09:34.571107+00	1	\N	{"tax_rate": 0.0}	t	f
3252	TAX_GROUP	Tax Group	EC Purchase Goods Zero Rate	tgXpOAMeNMux	2022-09-29 12:09:34.571177+00	2022-09-29 12:09:34.571206+00	1	\N	{"tax_rate": 0.0}	t	f
3253	TAX_GROUP	Tax Group	UK Import Services Exempt Rate	tgzgsasJ22yi	2022-09-29 12:09:34.571275+00	2022-09-29 12:09:34.571304+00	1	\N	{"tax_rate": 0.0}	t	f
3254	TAX_GROUP	Tax Group	EC Purchase Services Exempt Rate	tgzxd7JcZbz0	2022-09-29 12:09:34.571374+00	2022-09-29 12:09:34.571403+00	1	\N	{"tax_rate": 0.0}	t	f
2747	TAX_GROUP	Tax Group	UK Purchase Services Reduced Rate	tg9Q7Ppb49qU	2022-09-20 08:39:11.631836+00	2022-09-20 08:39:11.631913+00	1	\N	{"tax_rate": 0.05}	t	f
2909	TAX_GROUP	Tax Group	UK Purchase Services Standard Rate	tgp3usmS2kNN	2022-09-20 08:39:11.976251+00	2022-09-20 08:39:11.976278+00	1	\N	{"tax_rate": 0.2}	t	f
3231	TAX_GROUP	Tax Group	UK Purchase Services Zero Rate	tgb414CpV8wg	2022-09-29 12:09:34.562494+00	2022-09-29 12:09:34.562523+00	1	\N	{"tax_rate": 0.0}	t	f
3244	TAX_GROUP	Tax Group	W4 Withholding Tax	tgrpuUs8G1x2	2022-09-29 12:09:34.570298+00	2022-09-29 12:09:34.570327+00	1	\N	{"tax_rate": 0.0}	t	f
97	CATEGORY	Category	Xero Expense Account	192750	2022-09-20 08:39:03.372626+00	2022-09-20 08:39:03.372656+00	1	t	\N	f	f
98	CATEGORY	Category	New Aus	192534	2022-09-20 08:39:03.372716+00	2022-09-20 08:39:03.372745+00	1	t	\N	f	f
99	CATEGORY	Category	Final Aus Category	192535	2022-09-20 08:39:03.372805+00	2022-09-20 08:39:03.372834+00	1	t	\N	f	f
100	CATEGORY	Category	Nilesh Pant	192536	2022-09-20 08:39:03.372895+00	2022-09-20 08:39:03.372924+00	1	t	\N	f	f
101	CATEGORY	Category	Material purchase	191262	2022-09-20 08:39:03.373338+00	2022-09-20 08:39:03.373381+00	1	t	\N	f	f
102	CATEGORY	Category	Nilesh	184628	2022-09-20 08:39:03.373469+00	2022-09-20 08:39:03.37348+00	1	t	\N	f	f
107	CATEGORY	Category	Penalties & Settlements	163672	2022-09-20 08:39:03.374574+00	2022-09-20 08:39:03.374595+00	1	t	\N	f	f
108	CATEGORY	Category	Reconciliation Discrepancies	163673	2022-09-20 08:39:03.37465+00	2022-09-20 08:39:03.374671+00	1	t	\N	f	f
109	CATEGORY	Category	Checking	162001	2022-09-20 08:39:03.375565+00	2022-09-20 08:39:03.375613+00	1	t	\N	f	f
110	CATEGORY	Category	Savings	162002	2022-09-20 08:39:03.375782+00	2022-09-20 08:39:03.375809+00	1	t	\N	f	f
111	CATEGORY	Category	Advertising/Promotional	161875	2022-09-20 08:39:03.375861+00	2022-09-20 08:39:03.375882+00	1	t	\N	f	f
112	CATEGORY	Category	UK Expense Category	157669	2022-09-20 08:39:03.375971+00	2022-09-20 08:39:03.376371+00	1	t	\N	f	f
113	CATEGORY	Category	GST Paid	157846	2022-09-20 08:39:03.376985+00	2022-09-20 08:39:03.377032+00	1	t	\N	f	f
114	CATEGORY	Category	LCT Paid	157847	2022-09-20 08:39:03.377118+00	2022-09-20 08:39:03.377151+00	1	t	\N	f	f
115	CATEGORY	Category	WET Paid	157848	2022-09-20 08:39:03.378156+00	2022-09-20 08:39:03.378195+00	1	t	\N	f	f
116	CATEGORY	Category	ABN Withholding	157849	2022-09-20 08:39:03.378272+00	2022-09-20 08:39:03.378304+00	1	t	\N	f	f
117	CATEGORY	Category	Pay As You Go Withholding	157850	2022-09-20 08:39:03.378372+00	2022-09-20 08:39:03.378402+00	1	t	\N	f	f
118	CATEGORY	Category	VAT on Purchases	157851	2022-09-20 08:39:03.411993+00	2022-09-20 08:39:03.412058+00	1	t	\N	f	f
119	CATEGORY	Category	UK Expense Acct	157852	2022-09-20 08:39:03.414181+00	2022-09-20 08:39:03.414486+00	1	t	\N	f	f
120	CATEGORY	Category	UK EXP Account	157853	2022-09-20 08:39:03.414712+00	2022-09-20 08:39:03.414802+00	1	t	\N	f	f
121	CATEGORY	Category	Meals and Entertainment	135593	2022-09-20 08:39:03.414923+00	2022-09-20 08:39:03.414967+00	1	t	\N	f	f
122	CATEGORY	Category	Travel - Automobile	149798	2022-09-20 08:39:03.415097+00	2022-09-20 08:39:03.415139+00	1	t	\N	f	f
123	CATEGORY	Category	Aus Category	149228	2022-09-20 08:39:03.417914+00	2022-09-20 08:39:03.418009+00	1	t	\N	f	f
124	CATEGORY	Category	Bank Charges	135543	2022-09-20 08:39:03.418187+00	2022-09-20 08:39:03.418245+00	1	t	\N	f	f
125	CATEGORY	Category	Dues and Subscriptions	136468	2022-09-20 08:39:03.418374+00	2022-09-20 08:39:03.418424+00	1	t	\N	f	f
126	CATEGORY	Category	New Category	147927	2022-09-20 08:39:03.419031+00	2022-09-20 08:39:03.419575+00	1	t	\N	f	f
127	CATEGORY	Category	Travel expenses - selling expenses	147504	2022-09-20 08:39:03.419723+00	2022-09-20 08:39:03.419766+00	1	t	\N	f	f
18	CATEGORY	Category	post malone	208625	2022-09-20 08:39:03.250297+00	2022-09-20 08:39:03.25067+00	1	t	\N	f	f
19	CATEGORY	Category	Repair & Maintenance	208626	2022-09-20 08:39:03.250788+00	2022-09-20 08:39:03.250837+00	1	t	\N	f	f
28	CATEGORY	Category	KGF	208254	2022-09-20 08:39:03.252684+00	2022-09-20 08:39:03.252713+00	1	t	\N	f	f
29	CATEGORY	Category	Business Expense	208255	2022-09-20 08:39:03.252773+00	2022-09-20 08:39:03.252802+00	1	t	\N	f	f
30	CATEGORY	Category	Office/General Administrative Expenses	208256	2022-09-20 08:39:03.252863+00	2022-09-20 08:39:03.252892+00	1	t	\N	f	f
31	CATEGORY	Category	Entertainment	135450	2022-09-20 08:39:03.252953+00	2022-09-20 08:39:03.252981+00	1	t	\N	f	f
32	CATEGORY	Category	Rent	135556	2022-09-20 08:39:03.253041+00	2022-09-20 08:39:03.25307+00	1	t	\N	f	f
33	CATEGORY	Category	Insurance	135591	2022-09-20 08:39:03.253221+00	2022-09-20 08:39:03.253263+00	1	t	\N	f	f
34	CATEGORY	Category	Repairs and Maintenance	135594	2022-09-20 08:39:03.25333+00	2022-09-20 08:39:03.253359+00	1	t	\N	f	f
35	CATEGORY	Category	Interest Expense	135621	2022-09-20 08:39:03.253421+00	2022-09-20 08:39:03.253451+00	1	t	\N	f	f
36	CATEGORY	Category	Advertising	135716	2022-09-20 08:39:03.253511+00	2022-09-20 08:39:03.253541+00	1	t	\N	f	f
37	CATEGORY	Category	Office Expenses	135742	2022-09-20 08:39:03.253632+00	2022-09-20 08:39:03.253677+00	1	t	\N	f	f
38	CATEGORY	Category	Purchases	135747	2022-09-20 08:39:03.254086+00	2022-09-20 08:39:03.254134+00	1	t	\N	f	f
39	CATEGORY	Category	Cost of Goods Sold	135910	2022-09-20 08:39:03.254605+00	2022-09-20 08:39:03.254737+00	1	t	\N	f	f
40	CATEGORY	Category	Bank Fees	135991	2022-09-20 08:39:03.254859+00	2022-09-20 08:39:03.254895+00	1	t	\N	f	f
41	CATEGORY	Category	Cleaning	135992	2022-09-20 08:39:03.254966+00	2022-09-20 08:39:03.254996+00	1	t	\N	f	f
42	CATEGORY	Category	Consulting & Accounting	135993	2022-09-20 08:39:03.255064+00	2022-09-20 08:39:03.2551+00	1	t	\N	f	f
43	CATEGORY	Category	Depreciation	135994	2022-09-20 08:39:03.255232+00	2022-09-20 08:39:03.255675+00	1	t	\N	f	f
44	CATEGORY	Category	Freight & Courier	135995	2022-09-20 08:39:03.255887+00	2022-09-20 08:39:03.255941+00	1	t	\N	f	f
20	CATEGORY	Category	Mileage	135452	2022-09-20 08:39:03.250996+00	2022-09-20 08:39:03.251038+00	1	t	\N	t	f
21	CATEGORY	Category	Per Diem	135454	2022-09-20 08:39:03.251154+00	2022-09-20 08:39:03.251197+00	1	t	\N	t	f
46	CATEGORY	Category	Legal expenses	135997	2022-09-20 08:39:03.25644+00	2022-09-20 08:39:03.256483+00	1	t	\N	f	f
47	CATEGORY	Category	Light, Power, Heating	135998	2022-09-20 08:39:03.256605+00	2022-09-20 08:39:03.256647+00	1	t	\N	f	f
48	CATEGORY	Category	Motor Vehicle Expenses	135999	2022-09-20 08:39:03.256754+00	2022-09-20 08:39:03.2568+00	1	t	\N	f	f
49	CATEGORY	Category	Printing & Stationery	136000	2022-09-20 08:39:03.257278+00	2022-09-20 08:39:03.257498+00	1	t	\N	f	f
50	CATEGORY	Category	Wages and Salaries	136001	2022-09-20 08:39:03.257661+00	2022-09-20 08:39:03.257702+00	1	t	\N	f	f
51	CATEGORY	Category	Superannuation	136002	2022-09-20 08:39:03.257791+00	2022-09-20 08:39:03.257821+00	1	t	\N	f	f
52	CATEGORY	Category	Subscriptions	136003	2022-09-20 08:39:03.257917+00	2022-09-20 08:39:03.25809+00	1	t	\N	f	f
53	CATEGORY	Category	Telephone & Internet	136004	2022-09-20 08:39:03.258317+00	2022-09-20 08:39:03.258371+00	1	t	\N	f	f
54	CATEGORY	Category	Travel - National	136005	2022-09-20 08:39:03.2585+00	2022-09-20 08:39:03.258545+00	1	t	\N	f	f
55	CATEGORY	Category	Travel - International	136006	2022-09-20 08:39:03.258774+00	2022-09-20 08:39:03.258809+00	1	t	\N	f	f
56	CATEGORY	Category	Bank Revaluations	136007	2022-09-20 08:39:03.258961+00	2022-09-20 08:39:03.258992+00	1	t	\N	f	f
57	CATEGORY	Category	Unrealised Currency Gains	136008	2022-09-20 08:39:03.259066+00	2022-09-20 08:39:03.259083+00	1	t	\N	f	f
58	CATEGORY	Category	Realised Currency Gains	136009	2022-09-20 08:39:03.259153+00	2022-09-20 08:39:03.259184+00	1	t	\N	f	f
59	CATEGORY	Category	Income Tax Expense	136010	2022-09-20 08:39:03.259538+00	2022-09-20 08:39:03.259582+00	1	t	\N	f	f
60	CATEGORY	Category	9KAP9QWA44 / Turbo charged	195547	2022-09-20 08:39:03.260113+00	2022-09-20 08:39:03.260391+00	1	t	\N	f	f
61	CATEGORY	Category	CUBSMXQ74V / Turbo charged	194407	2022-09-20 08:39:03.260555+00	2022-09-20 08:39:03.260593+00	1	t	\N	f	f
62	CATEGORY	Category	7TF6ZC4WT9 / Turbo charged	194406	2022-09-20 08:39:03.260696+00	2022-09-20 08:39:03.26074+00	1	t	\N	f	f
63	CATEGORY	Category	6W2VT8W7SC / Turbo charged	194401	2022-09-20 08:39:03.260851+00	2022-09-20 08:39:03.260891+00	1	t	\N	f	f
64	CATEGORY	Category	XKZTXD6J07 / Turbo charged	194400	2022-09-20 08:39:03.261027+00	2022-09-20 08:39:03.261772+00	1	t	\N	f	f
65	CATEGORY	Category	T5G8M4IVT8 / Turbo charged	194399	2022-09-20 08:39:03.261854+00	2022-09-20 08:39:03.261871+00	1	t	\N	f	f
66	CATEGORY	Category	MGCYQRWOJ8 / Turbo charged	194398	2022-09-20 08:39:03.261923+00	2022-09-20 08:39:03.261952+00	1	t	\N	f	f
67	CATEGORY	Category	GP2UXTORT6 / Turbo charged	194397	2022-09-20 08:39:03.262033+00	2022-09-20 08:39:03.262094+00	1	t	\N	f	f
68	CATEGORY	Category	M75YLYFLX2 / Turbo charged	194396	2022-09-20 08:39:03.329636+00	2022-09-20 08:39:03.329682+00	1	t	\N	f	f
69	CATEGORY	Category	E2ZA5DOLZP / Turbo charged	194395	2022-09-20 08:39:03.329927+00	2022-09-20 08:39:03.33875+00	1	t	\N	f	f
70	CATEGORY	Category	N234JZCM07 / Turbo charged	194394	2022-09-20 08:39:03.338857+00	2022-09-20 08:39:03.338889+00	1	t	\N	f	f
71	CATEGORY	Category	VNISXKB26C / Turbo charged	194393	2022-09-20 08:39:03.338952+00	2022-09-20 08:39:03.338982+00	1	t	\N	f	f
72	CATEGORY	Category	JYJHRR8B69 / Turbo charged	194359	2022-09-20 08:39:03.339043+00	2022-09-20 08:39:03.339073+00	1	t	\N	f	f
73	CATEGORY	Category	OONDUAK3WT / Turbo charged	194332	2022-09-20 08:39:03.34269+00	2022-09-20 08:39:03.34275+00	1	t	\N	f	f
74	CATEGORY	Category	Q5OGEJBTKM / Turbo charged	194314	2022-09-20 08:39:03.342842+00	2022-09-20 08:39:03.342874+00	1	t	\N	f	f
75	CATEGORY	Category	SOYMBT74SM / Turbo charged	194302	2022-09-20 08:39:03.346765+00	2022-09-20 08:39:03.346885+00	1	t	\N	f	f
76	CATEGORY	Category	1PKB8P46QU / Turbo charged	194251	2022-09-20 08:39:03.349897+00	2022-09-20 08:39:03.349946+00	1	t	\N	f	f
77	CATEGORY	Category	R3BO0U5YZF / Turbo charged	194245	2022-09-20 08:39:03.350028+00	2022-09-20 08:39:03.350059+00	1	t	\N	f	f
78	CATEGORY	Category	Workers Compensation	193901	2022-09-20 08:39:03.35022+00	2022-09-20 08:39:03.350246+00	1	t	\N	f	f
79	CATEGORY	Category	Cost of Labor	193902	2022-09-20 08:39:03.350308+00	2022-09-20 08:39:03.350338+00	1	t	\N	f	f
80	CATEGORY	Category	Installation	193903	2022-09-20 08:39:03.35355+00	2022-09-20 08:39:03.354077+00	1	t	\N	f	f
81	CATEGORY	Category	Maintenance and Repairs	193904	2022-09-20 08:39:03.354328+00	2022-09-20 08:39:03.354365+00	1	t	\N	f	f
82	CATEGORY	Category	Job Materials	193905	2022-09-20 08:39:03.354428+00	2022-09-20 08:39:03.354449+00	1	t	\N	f	f
83	CATEGORY	Category	Decks and Patios	193906	2022-09-20 08:39:03.354501+00	2022-09-20 08:39:03.37025+00	1	t	\N	f	f
84	CATEGORY	Category	Fountain and Garden Lighting	193907	2022-09-20 08:39:03.37036+00	2022-09-20 08:39:03.370385+00	1	t	\N	f	f
85	CATEGORY	Category	Plants and Soil	193908	2022-09-20 08:39:03.370962+00	2022-09-20 08:39:03.371006+00	1	t	\N	f	f
86	CATEGORY	Category	Sprinklers and Drip Systems	193909	2022-09-20 08:39:03.371075+00	2022-09-20 08:39:03.371104+00	1	t	\N	f	f
87	CATEGORY	Category	Permits	193910	2022-09-20 08:39:03.371165+00	2022-09-20 08:39:03.371195+00	1	t	\N	f	f
88	CATEGORY	Category	Bookkeeper	193911	2022-09-20 08:39:03.371255+00	2022-09-20 08:39:03.371306+00	1	t	\N	f	f
89	CATEGORY	Category	Lawyer	193912	2022-09-20 08:39:03.371505+00	2022-09-20 08:39:03.371529+00	1	t	\N	f	f
90	CATEGORY	Category	Building Repairs	193913	2022-09-20 08:39:03.371625+00	2022-09-20 08:39:03.371656+00	1	t	\N	f	f
91	CATEGORY	Category	Computer Repairs	193914	2022-09-20 08:39:03.372043+00	2022-09-20 08:39:03.372065+00	1	t	\N	f	f
92	CATEGORY	Category	Equipment Repairs	193915	2022-09-20 08:39:03.372118+00	2022-09-20 08:39:03.372148+00	1	t	\N	f	f
93	CATEGORY	Category	Gas and Electric	193916	2022-09-20 08:39:03.37221+00	2022-09-20 08:39:03.372239+00	1	t	\N	f	f
94	CATEGORY	Category	Telephone	193917	2022-09-20 08:39:03.372303+00	2022-09-20 08:39:03.372333+00	1	t	\N	f	f
95	CATEGORY	Category	xero prod	193480	2022-09-20 08:39:03.372419+00	2022-09-20 08:39:03.372449+00	1	t	\N	f	f
96	CATEGORY	Category	Sravan Expense Account	192749	2022-09-20 08:39:03.372537+00	2022-09-20 08:39:03.372566+00	1	t	\N	f	f
128	CATEGORY	Category	Uncategorised Expense	147505	2022-09-20 08:39:03.419866+00	2022-09-20 08:39:03.419907+00	1	t	\N	f	f
129	CATEGORY	Category	Utilities - Electric & Gas	147506	2022-09-20 08:39:03.420004+00	2022-09-20 08:39:03.420044+00	1	t	\N	f	f
130	CATEGORY	Category	Utilities - Water	147507	2022-09-20 08:39:03.420138+00	2022-09-20 08:39:03.420178+00	1	t	\N	f	f
131	CATEGORY	Category	Wage expenses	147508	2022-09-20 08:39:03.420272+00	2022-09-20 08:39:03.420312+00	1	t	\N	f	f
132	CATEGORY	Category	Amortisation (and depreciation) expense	147479	2022-09-20 08:39:03.420405+00	2022-09-20 08:39:03.420446+00	1	t	\N	f	f
133	CATEGORY	Category	Bad debts	147480	2022-09-20 08:39:03.420674+00	2022-09-20 08:39:03.42301+00	1	t	\N	f	f
134	CATEGORY	Category	BAS Expense	147482	2022-09-20 08:39:03.423123+00	2022-09-20 08:39:03.425598+00	1	t	\N	f	f
135	CATEGORY	Category	Commissions and fees	147483	2022-09-20 08:39:03.425923+00	2022-09-20 08:39:03.425981+00	1	t	\N	f	f
136	CATEGORY	Category	Communication Expense - Fixed	147484	2022-09-20 08:39:03.426099+00	2022-09-20 08:39:03.426144+00	1	t	\N	f	f
137	CATEGORY	Category	Insurance - Disability	147488	2022-09-20 08:39:03.42624+00	2022-09-20 08:39:03.426283+00	1	t	\N	f	f
138	CATEGORY	Category	Insurance - General	147489	2022-09-20 08:39:03.426384+00	2022-09-20 08:39:03.427194+00	1	t	\N	f	f
139	CATEGORY	Category	Insurance - Liability	147490	2022-09-20 08:39:03.4273+00	2022-09-20 08:39:03.428789+00	1	t	\N	f	f
140	CATEGORY	Category	Legal and professional fees	147492	2022-09-20 08:39:03.428884+00	2022-09-20 08:39:03.428915+00	1	t	\N	f	f
141	CATEGORY	Category	Loss on discontinued operations, net of tax	147493	2022-09-20 08:39:03.428979+00	2022-09-20 08:39:03.429009+00	1	t	\N	f	f
142	CATEGORY	Category	Management compensation	147494	2022-09-20 08:39:03.429071+00	2022-09-20 08:39:03.429101+00	1	t	\N	f	f
143	CATEGORY	Category	Other general and administrative expenses	147497	2022-09-20 08:39:03.429163+00	2022-09-20 08:39:03.429192+00	1	t	\N	f	f
144	CATEGORY	Category	Other selling expenses	147498	2022-09-20 08:39:03.429254+00	2022-09-20 08:39:03.429284+00	1	t	\N	f	f
145	CATEGORY	Category	Other Types of Expenses-Advertising Expenses	147499	2022-09-20 08:39:03.429344+00	2022-09-20 08:39:03.429374+00	1	t	\N	f	f
366	CATEGORY	Category	test	137949	2022-09-20 08:39:05.302162+00	2022-09-20 08:39:05.302194+00	1	t	\N	f	f
146	CATEGORY	Category	Rent or lease payments	147500	2022-09-20 08:39:03.429435+00	2022-09-20 08:39:03.429464+00	1	t	\N	f	f
147	CATEGORY	Category	Shipping and delivery expense	147501	2022-09-20 08:39:03.429524+00	2022-09-20 08:39:03.429554+00	1	t	\N	f	f
148	CATEGORY	Category	Stationery and printing	147502	2022-09-20 08:39:03.429614+00	2022-09-20 08:39:03.429643+00	1	t	\N	f	f
149	CATEGORY	Category	Travel expenses - general and admin expenses	147503	2022-09-20 08:39:03.429704+00	2022-09-20 08:39:03.429734+00	1	t	\N	f	f
150	CATEGORY	Category	Office Supplies	135448	2022-09-20 08:39:03.429795+00	2022-09-20 08:39:03.429825+00	1	t	\N	f	f
151	CATEGORY	Category	Movies	145416	2022-09-20 08:39:03.429886+00	2022-09-20 08:39:03.429915+00	1	t	\N	f	f
152	CATEGORY	Category	Dues Expenses from Intacct	141965	2022-09-20 08:39:03.429976+00	2022-09-20 08:39:03.430005+00	1	t	\N	f	f
153	CATEGORY	Category	Workers' compensation	135887	2022-09-20 08:39:03.430066+00	2022-09-20 08:39:03.430096+00	1	t	\N	f	f
154	CATEGORY	Category	Disability	135888	2022-09-20 08:39:03.430438+00	2022-09-20 08:39:03.431988+00	1	t	\N	f	f
155	CATEGORY	Category	Miscellaneous Expense	135889	2022-09-20 08:39:03.432079+00	2022-09-20 08:39:03.432108+00	1	t	\N	f	f
156	CATEGORY	Category	Office Expense	135890	2022-09-20 08:39:03.43217+00	2022-09-20 08:39:03.432199+00	1	t	\N	f	f
157	CATEGORY	Category	Outside Services	135891	2022-09-20 08:39:03.43226+00	2022-09-20 08:39:03.432289+00	1	t	\N	f	f
158	CATEGORY	Category	Postage & Delivery	135892	2022-09-20 08:39:03.432363+00	2022-09-20 08:39:03.432392+00	1	t	\N	f	f
159	CATEGORY	Category	Professional Fees	135893	2022-09-20 08:39:03.432453+00	2022-09-20 08:39:03.432482+00	1	t	\N	f	f
160	CATEGORY	Category	Rent Expense	135894	2022-09-20 08:39:03.432542+00	2022-09-20 08:39:03.432571+00	1	t	\N	f	f
161	CATEGORY	Category	Repairs & Maintenance	135895	2022-09-20 08:39:03.432631+00	2022-09-20 08:39:03.43266+00	1	t	\N	f	f
162	CATEGORY	Category	Supplies Expense	135896	2022-09-20 08:39:03.432721+00	2022-09-20 08:39:03.43275+00	1	t	\N	f	f
163	CATEGORY	Category	Taxes & Licenses-Other	135897	2022-09-20 08:39:03.43281+00	2022-09-20 08:39:03.43284+00	1	t	\N	f	f
164	CATEGORY	Category	Business	135898	2022-09-20 08:39:03.4329+00	2022-09-20 08:39:03.432929+00	1	t	\N	f	f
165	CATEGORY	Category	Property	135899	2022-09-20 08:39:03.43299+00	2022-09-20 08:39:03.433019+00	1	t	\N	f	f
166	CATEGORY	Category	Vehicle Registration	135900	2022-09-20 08:39:03.433079+00	2022-09-20 08:39:03.433108+00	1	t	\N	f	f
167	CATEGORY	Category	Telephone Expense	135901	2022-09-20 08:39:03.433168+00	2022-09-20 08:39:03.433197+00	1	t	\N	f	f
168	CATEGORY	Category	Regular Service	135902	2022-09-20 08:39:03.45076+00	2022-09-20 08:39:03.450802+00	1	t	\N	f	f
169	CATEGORY	Category	Pager	135903	2022-09-20 08:39:03.450865+00	2022-09-20 08:39:03.450895+00	1	t	\N	f	f
170	CATEGORY	Category	Cellular	135904	2022-09-20 08:39:03.450956+00	2022-09-20 08:39:03.450985+00	1	t	\N	f	f
171	CATEGORY	Category	Online Fees	135905	2022-09-20 08:39:03.451045+00	2022-09-20 08:39:03.451078+00	1	t	\N	f	f
172	CATEGORY	Category	Gain (loss) on Sale of Assets	135906	2022-09-20 08:39:03.45114+00	2022-09-20 08:39:03.451169+00	1	t	\N	f	f
173	CATEGORY	Category	Salaries & Wages Expense	135907	2022-09-20 08:39:03.45123+00	2022-09-20 08:39:03.451259+00	1	t	\N	f	f
174	CATEGORY	Category	Advances Paid	135908	2022-09-20 08:39:03.45132+00	2022-09-20 08:39:03.451349+00	1	t	\N	f	f
175	CATEGORY	Category	Inventory Asset	135909	2022-09-20 08:39:03.451409+00	2022-09-20 08:39:03.451438+00	1	t	\N	f	f
176	CATEGORY	Category	Furniture & Fixtures Expense	135911	2022-09-20 08:39:03.451499+00	2022-09-20 08:39:03.451528+00	1	t	\N	f	f
177	CATEGORY	Category	Accounting	135912	2022-09-20 08:39:03.451588+00	2022-09-20 08:39:03.451618+00	1	t	\N	f	f
179	CATEGORY	Category	Exchange Rate Variance	135914	2022-09-20 08:39:03.451768+00	2022-09-20 08:39:03.451797+00	1	t	\N	f	f
180	CATEGORY	Category	Duty Expense	135915	2022-09-20 08:39:03.451857+00	2022-09-20 08:39:03.451887+00	1	t	\N	f	f
181	CATEGORY	Category	Freight Expense	135916	2022-09-20 08:39:03.451947+00	2022-09-20 08:39:03.451976+00	1	t	\N	f	f
182	CATEGORY	Category	Inventory Returned Not Credited	135917	2022-09-20 08:39:03.452931+00	2022-09-20 08:39:03.453006+00	1	t	\N	f	f
183	CATEGORY	Category	Damaged Goods	135918	2022-09-20 08:39:03.453815+00	2022-09-20 08:39:03.454107+00	1	t	\N	f	f
184	CATEGORY	Category	Inventory Write Offs	135919	2022-09-20 08:39:03.45418+00	2022-09-20 08:39:03.454211+00	1	t	\N	f	f
185	CATEGORY	Category	Inventory In Transit	135920	2022-09-20 08:39:03.454273+00	2022-09-20 08:39:03.454303+00	1	t	\N	f	f
186	CATEGORY	Category	Bill Quantity Variance	135921	2022-09-20 08:39:03.454365+00	2022-09-20 08:39:03.454394+00	1	t	\N	f	f
187	CATEGORY	Category	Bill Price Variance	135922	2022-09-20 08:39:03.454455+00	2022-09-20 08:39:03.454704+00	1	t	\N	f	f
188	CATEGORY	Category	Job Expenses:Equipment Rental	135726	2022-09-20 08:39:03.454943+00	2022-09-20 08:39:03.45498+00	1	t	\N	f	f
189	CATEGORY	Category	Job Expenses:Job Materials	135727	2022-09-20 08:39:03.455042+00	2022-09-20 08:39:03.45508+00	1	t	\N	f	f
190	CATEGORY	Category	Job Expenses:Job Materials:Decks and Patios	135728	2022-09-20 08:39:03.455139+00	2022-09-20 08:39:03.455161+00	1	t	\N	f	f
191	CATEGORY	Category	Job Expenses:Job Materials:Fountain and Garden Lighting	135729	2022-09-20 08:39:03.455226+00	2022-09-20 08:39:03.455245+00	1	t	\N	f	f
192	CATEGORY	Category	Job Expenses:Job Materials:Plants and Soil	135730	2022-09-20 08:39:03.455297+00	2022-09-20 08:39:03.455451+00	1	t	\N	f	f
193	CATEGORY	Category	Job Expenses:Job Materials:Sprinklers and Drip Systems	135731	2022-09-20 08:39:03.455542+00	2022-09-20 08:39:03.455908+00	1	t	\N	f	f
194	CATEGORY	Category	Job Expenses:Permits	135732	2022-09-20 08:39:03.456373+00	2022-09-20 08:39:03.456414+00	1	t	\N	f	f
195	CATEGORY	Category	Legal & Professional Fees	135733	2022-09-20 08:39:03.456526+00	2022-09-20 08:39:03.456663+00	1	t	\N	f	f
196	CATEGORY	Category	Legal & Professional Fees:Accounting	135734	2022-09-20 08:39:03.456744+00	2022-09-20 08:39:03.456773+00	1	t	\N	f	f
197	CATEGORY	Category	Legal & Professional Fees:Bookkeeper	135735	2022-09-20 08:39:03.456835+00	2022-09-20 08:39:03.456864+00	1	t	\N	f	f
198	CATEGORY	Category	Legal & Professional Fees:Lawyer	135736	2022-09-20 08:39:03.456925+00	2022-09-20 08:39:03.456954+00	1	t	\N	f	f
199	CATEGORY	Category	Maintenance and Repair	135737	2022-09-20 08:39:03.457054+00	2022-09-20 08:39:03.457112+00	1	t	\N	f	f
200	CATEGORY	Category	Maintenance and Repair:Building Repairs	135738	2022-09-20 08:39:03.457644+00	2022-09-20 08:39:03.457679+00	1	t	\N	f	f
201	CATEGORY	Category	Maintenance and Repair:Computer Repairs	135739	2022-09-20 08:39:03.457742+00	2022-09-20 08:39:03.457771+00	1	t	\N	f	f
202	CATEGORY	Category	Maintenance and Repair:Equipment Repairs	135740	2022-09-20 08:39:03.457823+00	2022-09-20 08:39:03.457844+00	1	t	\N	f	f
203	CATEGORY	Category	Office-General Administrative Expenses	135745	2022-09-20 08:39:03.458018+00	2022-09-20 08:39:03.458061+00	1	t	\N	f	f
204	CATEGORY	Category	Promotional	135746	2022-09-20 08:39:03.458126+00	2022-09-20 08:39:03.45815+00	1	t	\N	f	f
205	CATEGORY	Category	Rent or Lease	135748	2022-09-20 08:39:03.458202+00	2022-09-20 08:39:03.45899+00	1	t	\N	f	f
206	CATEGORY	Category	Stationery & Printing	135749	2022-09-20 08:39:03.459128+00	2022-09-20 08:39:03.459171+00	1	t	\N	f	f
207	CATEGORY	Category	Supplies Test 2	135750	2022-09-20 08:39:03.460106+00	2022-09-20 08:39:03.46023+00	1	t	\N	f	f
208	CATEGORY	Category	Taxes & Licenses	135751	2022-09-20 08:39:03.46074+00	2022-09-20 08:39:03.460773+00	1	t	\N	f	f
209	CATEGORY	Category	Test Staging	135753	2022-09-20 08:39:03.460824+00	2022-09-20 08:39:03.460845+00	1	t	\N	f	f
210	CATEGORY	Category	Insurance:Workers Compensation	135754	2022-09-20 08:39:03.460906+00	2022-09-20 08:39:03.460935+00	1	t	\N	f	f
211	CATEGORY	Category	Job Expenses	135755	2022-09-20 08:39:03.461141+00	2022-09-20 08:39:03.46118+00	1	t	\N	f	f
212	CATEGORY	Category	Job Expenses:Cost of Labor	135756	2022-09-20 08:39:03.461252+00	2022-09-20 08:39:03.461282+00	1	t	\N	f	f
213	CATEGORY	Category	Travel Meals	135757	2022-09-20 08:39:03.461365+00	2022-09-20 08:39:03.461394+00	1	t	\N	f	f
214	CATEGORY	Category	Unapplied Cash Bill Payment Expense	135758	2022-09-20 08:39:03.461455+00	2022-09-20 08:39:03.461476+00	1	t	\N	f	f
215	CATEGORY	Category	Uncategorized Expense	135759	2022-09-20 08:39:03.461528+00	2022-09-20 08:39:03.461549+00	1	t	\N	f	f
216	CATEGORY	Category	Utilities:Gas and Electric	135760	2022-09-20 08:39:03.46161+00	2022-09-20 08:39:03.461639+00	1	t	\N	f	f
217	CATEGORY	Category	Utilities:Telephone	135761	2022-09-20 08:39:03.4617+00	2022-09-20 08:39:03.46313+00	1	t	\N	f	f
218	CATEGORY	Category	Prepaid Expenses	135871	2022-09-20 08:39:05.126669+00	2022-09-20 08:39:05.126718+00	1	t	\N	f	f
219	CATEGORY	Category	Prepaid Income Taxes	135872	2022-09-20 08:39:05.126792+00	2022-09-20 08:39:05.126819+00	1	t	\N	f	f
220	CATEGORY	Category	Note Receivable-Current	135873	2022-09-20 08:39:05.126881+00	2022-09-20 08:39:05.126931+00	1	t	\N	f	f
221	CATEGORY	Category	Merchandise	135874	2022-09-20 08:39:05.145405+00	2022-09-20 08:39:05.145453+00	1	t	\N	f	f
222	CATEGORY	Category	Service	135875	2022-09-20 08:39:05.145526+00	2022-09-20 08:39:05.145556+00	1	t	\N	f	f
223	CATEGORY	Category	Salaries & Wages	135876	2022-09-20 08:39:05.145618+00	2022-09-20 08:39:05.145647+00	1	t	\N	f	f
224	CATEGORY	Category	Other Direct Costs	135877	2022-09-20 08:39:05.145769+00	2022-09-20 08:39:05.145803+00	1	t	\N	f	f
225	CATEGORY	Category	Inventory Variance	135878	2022-09-20 08:39:05.145875+00	2022-09-20 08:39:05.145897+00	1	t	\N	f	f
226	CATEGORY	Category	Automobile Expense	135879	2022-09-20 08:39:05.14596+00	2022-09-20 08:39:05.14598+00	1	t	\N	f	f
227	CATEGORY	Category	Gas & Oil	135880	2022-09-20 08:39:05.146042+00	2022-09-20 08:39:05.146063+00	1	t	\N	f	f
228	CATEGORY	Category	Repairs	135881	2022-09-20 08:39:05.146115+00	2022-09-20 08:39:05.146144+00	1	t	\N	f	f
229	CATEGORY	Category	Bank Service Charges	135882	2022-09-20 08:39:05.146304+00	2022-09-20 08:39:05.146324+00	1	t	\N	f	f
230	CATEGORY	Category	Contributions	135883	2022-09-20 08:39:05.146376+00	2022-09-20 08:39:05.146405+00	1	t	\N	f	f
231	CATEGORY	Category	Freight & Delivery	135884	2022-09-20 08:39:05.146466+00	2022-09-20 08:39:05.146495+00	1	t	\N	f	f
232	CATEGORY	Category	Insurance Expense	135885	2022-09-20 08:39:05.14655+00	2022-09-20 08:39:05.146571+00	1	t	\N	f	f
233	CATEGORY	Category	Liability	135886	2022-09-20 08:39:05.146632+00	2022-09-20 08:39:05.146661+00	1	t	\N	f	f
234	CATEGORY	Category	ASHWIN MANUALLY ADDED THIS2	135550	2022-09-20 08:39:05.146721+00	2022-09-20 08:39:05.146744+00	1	t	\N	f	f
235	CATEGORY	Category	Fyle	135551	2022-09-20 08:39:05.146795+00	2022-09-20 08:39:05.146816+00	1	t	\N	f	f
236	CATEGORY	Category	Furniture & Fixtures	135612	2022-09-20 08:39:05.146876+00	2022-09-20 08:39:05.146898+00	1	t	\N	f	f
237	CATEGORY	Category	Accm.Depr. Furniture & Fixtures	135613	2022-09-20 08:39:05.14695+00	2022-09-20 08:39:05.146971+00	1	t	\N	f	f
238	CATEGORY	Category	Deferred Revenue Contra	135614	2022-09-20 08:39:05.147023+00	2022-09-20 08:39:05.147052+00	1	t	\N	f	f
239	CATEGORY	Category	Deferred Revenue	135615	2022-09-20 08:39:05.147112+00	2022-09-20 08:39:05.147141+00	1	t	\N	f	f
240	CATEGORY	Category	Due to Entity 300	135616	2022-09-20 08:39:05.147196+00	2022-09-20 08:39:05.147217+00	1	t	\N	f	f
241	CATEGORY	Category	Due to Entity 100	135617	2022-09-20 08:39:05.147268+00	2022-09-20 08:39:05.147386+00	1	t	\N	f	f
242	CATEGORY	Category	Due to Entity 200	135618	2022-09-20 08:39:05.147441+00	2022-09-20 08:39:05.147461+00	1	t	\N	f	f
243	CATEGORY	Category	Intercompany Payables	135619	2022-09-20 08:39:05.147522+00	2022-09-20 08:39:05.147551+00	1	t	\N	f	f
244	CATEGORY	Category	Interest Income	135620	2022-09-20 08:39:05.147603+00	2022-09-20 08:39:05.147615+00	1	t	\N	f	f
245	CATEGORY	Category	Intercompany Professional Fees	135622	2022-09-20 08:39:05.147657+00	2022-09-20 08:39:05.147678+00	1	t	\N	f	f
246	CATEGORY	Category	Amortization Expense	135623	2022-09-20 08:39:05.147738+00	2022-09-20 08:39:05.147767+00	1	t	\N	f	f
247	CATEGORY	Category	Revenue - Other	135624	2022-09-20 08:39:05.147827+00	2022-09-20 08:39:05.147856+00	1	t	\N	f	f
248	CATEGORY	Category	Payroll Taxes	135625	2022-09-20 08:39:05.147912+00	2022-09-20 08:39:05.147932+00	1	t	\N	f	f
249	CATEGORY	Category	Inventory	135626	2022-09-20 08:39:05.147993+00	2022-09-20 08:39:05.148022+00	1	t	\N	f	f
250	CATEGORY	Category	Inventory-Other	135627	2022-09-20 08:39:05.148083+00	2022-09-20 08:39:05.148106+00	1	t	\N	f	f
251	CATEGORY	Category	Inventory-Kits	135628	2022-09-20 08:39:05.148158+00	2022-09-20 08:39:05.148187+00	1	t	\N	f	f
252	CATEGORY	Category	Other Intangible Assets	135629	2022-09-20 08:39:05.152885+00	2022-09-20 08:39:05.152917+00	1	t	\N	f	f
253	CATEGORY	Category	Other Assets	135630	2022-09-20 08:39:05.15298+00	2022-09-20 08:39:05.153009+00	1	t	\N	f	f
254	CATEGORY	Category	COGS-Damage, Scrap, Spoilage	135635	2022-09-20 08:39:05.15307+00	2022-09-20 08:39:05.153098+00	1	t	\N	f	f
255	CATEGORY	Category	Excise Tax	135636	2022-09-20 08:39:05.153158+00	2022-09-20 08:39:05.153187+00	1	t	\N	f	f
256	CATEGORY	Category	Other Taxes	135637	2022-09-20 08:39:05.153247+00	2022-09-20 08:39:05.153276+00	1	t	\N	f	f
257	CATEGORY	Category	Other Expense	135638	2022-09-20 08:39:05.153336+00	2022-09-20 08:39:05.153365+00	1	t	\N	f	f
258	CATEGORY	Category	Other Income	135639	2022-09-20 08:39:05.153425+00	2022-09-20 08:39:05.153454+00	1	t	\N	f	f
259	CATEGORY	Category	AR-Retainage	135640	2022-09-20 08:39:05.153514+00	2022-09-20 08:39:05.153543+00	1	t	\N	f	f
260	CATEGORY	Category	Accounts Receivable	135641	2022-09-20 08:39:05.153603+00	2022-09-20 08:39:05.153632+00	1	t	\N	f	f
261	CATEGORY	Category	Accounts Receivable - Other	135642	2022-09-20 08:39:05.153692+00	2022-09-20 08:39:05.153721+00	1	t	\N	f	f
262	CATEGORY	Category	Accounts Payable - Employees	135643	2022-09-20 08:39:05.153782+00	2022-09-20 08:39:05.153811+00	1	t	\N	f	f
263	CATEGORY	Category	Accounts Payable	135644	2022-09-20 08:39:05.153871+00	2022-09-20 08:39:05.1539+00	1	t	\N	f	f
264	CATEGORY	Category	Software and Licenses	135645	2022-09-20 08:39:05.154337+00	2022-09-20 08:39:05.15437+00	1	t	\N	f	f
265	CATEGORY	Category	Utilities	135646	2022-09-20 08:39:05.158632+00	2022-09-20 08:39:05.158712+00	1	t	\N	f	f
266	CATEGORY	Category	ASHWIN MANUALLY ADDED THIS	135647	2022-09-20 08:39:05.15888+00	2022-09-20 08:39:05.158995+00	1	t	\N	f	f
267	CATEGORY	Category	Fyleasdads	135648	2022-09-20 08:39:05.159067+00	2022-09-20 08:39:05.159097+00	1	t	\N	f	f
268	CATEGORY	Category	Fyle Expenses	135652	2022-09-20 08:39:05.192844+00	2022-09-20 08:39:05.192885+00	1	t	\N	f	f
269	CATEGORY	Category	Fyle Expenses!	135655	2022-09-20 08:39:05.192949+00	2022-09-20 08:39:05.192979+00	1	t	\N	f	f
271	CATEGORY	Category	Automobile:Fuel	135718	2022-09-20 08:39:05.193129+00	2022-09-20 08:39:05.193158+00	1	t	\N	f	f
272	CATEGORY	Category	Commissions & fees	135719	2022-09-20 08:39:05.193219+00	2022-09-20 08:39:05.193248+00	1	t	\N	f	f
273	CATEGORY	Category	Disposal Fees	135720	2022-09-20 08:39:05.193546+00	2022-09-20 08:39:05.193587+00	1	t	\N	f	f
274	CATEGORY	Category	Dues & Subscriptions	135721	2022-09-20 08:39:05.193645+00	2022-09-20 08:39:05.193674+00	1	t	\N	f	f
275	CATEGORY	Category	Incremental Account	135723	2022-09-20 08:39:05.193735+00	2022-09-20 08:39:05.193771+00	1	t	\N	f	f
276	CATEGORY	Category	Job Expenses:Cost of Labor:Installation	135724	2022-09-20 08:39:05.193839+00	2022-09-20 08:39:05.193868+00	1	t	\N	f	f
277	CATEGORY	Category	Job Expenses:Cost of Labor:Maintenance and Repairs	135725	2022-09-20 08:39:05.193959+00	2022-09-20 08:39:05.193984+00	1	t	\N	f	f
278	CATEGORY	Category	Office Party	135462	2022-09-20 08:39:05.194037+00	2022-09-20 08:39:05.194063+00	1	t	\N	f	f
279	CATEGORY	Category	Flight	135463	2022-09-20 08:39:05.194115+00	2022-09-20 08:39:05.194136+00	1	t	\N	f	f
280	CATEGORY	Category	Software	135464	2022-09-20 08:39:05.194196+00	2022-09-20 08:39:05.194225+00	1	t	\N	f	f
281	CATEGORY	Category	Parking	135465	2022-09-20 08:39:05.194285+00	2022-09-20 08:39:05.194314+00	1	t	\N	f	f
282	CATEGORY	Category	Toll Charge	135466	2022-09-20 08:39:05.194375+00	2022-09-20 08:39:05.194404+00	1	t	\N	f	f
283	CATEGORY	Category	Tax	135467	2022-09-20 08:39:05.194464+00	2022-09-20 08:39:05.194687+00	1	t	\N	f	f
284	CATEGORY	Category	Training	135468	2022-09-20 08:39:05.196104+00	2022-09-20 08:39:05.196136+00	1	t	\N	f	f
285	CATEGORY	Category	Prepaid Insurance	135571	2022-09-20 08:39:05.196199+00	2022-09-20 08:39:05.196228+00	1	t	\N	f	f
286	CATEGORY	Category	Prepaid Rent	135572	2022-09-20 08:39:05.201638+00	2022-09-20 08:39:05.201693+00	1	t	\N	f	f
287	CATEGORY	Category	Prepaid Other	135573	2022-09-20 08:39:05.201779+00	2022-09-20 08:39:05.20181+00	1	t	\N	f	f
288	CATEGORY	Category	Employee Advances	135574	2022-09-20 08:39:05.201876+00	2022-09-20 08:39:05.201911+00	1	t	\N	f	f
289	CATEGORY	Category	Salaries Payable	135575	2022-09-20 08:39:05.201974+00	2022-09-20 08:39:05.202001+00	1	t	\N	f	f
290	CATEGORY	Category	Goods Received Not Invoiced (GRNI)	135576	2022-09-20 08:39:05.202044+00	2022-09-20 08:39:05.202062+00	1	t	\N	f	f
291	CATEGORY	Category	Estimated Landed Costs	135577	2022-09-20 08:39:05.202107+00	2022-09-20 08:39:05.202128+00	1	t	\N	f	f
292	CATEGORY	Category	Actual Landed Costs	135578	2022-09-20 08:39:05.202188+00	2022-09-20 08:39:05.20376+00	1	t	\N	f	f
293	CATEGORY	Category	Accrued Payroll Tax Payable	135579	2022-09-20 08:39:05.204396+00	2022-09-20 08:39:05.20444+00	1	t	\N	f	f
294	CATEGORY	Category	Accrued Sales Tax Payable	135580	2022-09-20 08:39:05.216346+00	2022-09-20 08:39:05.216391+00	1	t	\N	f	f
295	CATEGORY	Category	Company Credit Card Offset	135581	2022-09-20 08:39:05.216478+00	2022-09-20 08:39:05.216838+00	1	t	\N	f	f
296	CATEGORY	Category	Telecommunication Expense	135582	2022-09-20 08:39:05.217382+00	2022-09-20 08:39:05.217414+00	1	t	\N	f	f
297	CATEGORY	Category	Employee Deductions	135583	2022-09-20 08:39:05.21748+00	2022-09-20 08:39:05.21751+00	1	t	\N	f	f
298	CATEGORY	Category	Goodwill	135584	2022-09-20 08:39:05.217616+00	2022-09-20 08:39:05.217643+00	1	t	\N	f	f
299	CATEGORY	Category	Depreciation Expense	135585	2022-09-20 08:39:05.217705+00	2022-09-20 08:39:05.217826+00	1	t	\N	f	f
300	CATEGORY	Category	Revenue - Accessories	135586	2022-09-20 08:39:05.22703+00	2022-09-20 08:39:05.227054+00	1	t	\N	f	f
301	CATEGORY	Category	Revenue - Entry	135587	2022-09-20 08:39:05.227109+00	2022-09-20 08:39:05.228641+00	1	t	\N	f	f
302	CATEGORY	Category	Revenue - Surveillance	135588	2022-09-20 08:39:05.230883+00	2022-09-20 08:39:05.230913+00	1	t	\N	f	f
303	CATEGORY	Category	Marketing and Advertising	135589	2022-09-20 08:39:05.23097+00	2022-09-20 08:39:05.230991+00	1	t	\N	f	f
304	CATEGORY	Category	Trade Shows and Exhibits	135590	2022-09-20 08:39:05.231643+00	2022-09-20 08:39:05.231677+00	1	t	\N	f	f
305	CATEGORY	Category	Professional Fees Expense	135592	2022-09-20 08:39:05.23175+00	2022-09-20 08:39:05.23178+00	1	t	\N	f	f
306	CATEGORY	Category	Salaries and Wages	135595	2022-09-20 08:39:05.233143+00	2022-09-20 08:39:05.247716+00	1	t	\N	f	f
307	CATEGORY	Category	Gain for Sale of an asset	135596	2022-09-20 08:39:05.248035+00	2022-09-20 08:39:05.248064+00	1	t	\N	f	f
308	CATEGORY	Category	Dividends	135597	2022-09-20 08:39:05.248125+00	2022-09-20 08:39:05.248155+00	1	t	\N	f	f
309	CATEGORY	Category	SVB Checking	135598	2022-09-20 08:39:05.248226+00	2022-09-20 08:39:05.248257+00	1	t	\N	f	f
310	CATEGORY	Category	SVB Checking 2	135599	2022-09-20 08:39:05.248319+00	2022-09-20 08:39:05.248493+00	1	t	\N	f	f
311	CATEGORY	Category	Cash	135601	2022-09-20 08:39:05.248558+00	2022-09-20 08:39:05.248587+00	1	t	\N	f	f
312	CATEGORY	Category	Cash Equivalents	135602	2022-09-20 08:39:05.248645+00	2022-09-20 08:39:05.248666+00	1	t	\N	f	f
313	CATEGORY	Category	Investments and Securities	135603	2022-09-20 08:39:05.248719+00	2022-09-20 08:39:05.248736+00	1	t	\N	f	f
314	CATEGORY	Category	Due from Entity 200	135604	2022-09-20 08:39:05.248786+00	2022-09-20 08:39:05.248816+00	1	t	\N	f	f
315	CATEGORY	Category	Due from Entity 300	135605	2022-09-20 08:39:05.248887+00	2022-09-20 08:39:05.248916+00	1	t	\N	f	f
316	CATEGORY	Category	Due from Entity 100	135606	2022-09-20 08:39:05.248978+00	2022-09-20 08:39:05.249005+00	1	t	\N	f	f
317	CATEGORY	Category	Intercompany Receivables	135607	2022-09-20 08:39:05.249154+00	2022-09-20 08:39:05.249197+00	1	t	\N	f	f
318	CATEGORY	Category	Capitalized Software Costs	135608	2022-09-20 08:39:05.264043+00	2022-09-20 08:39:05.264112+00	1	t	\N	f	f
319	CATEGORY	Category	Buildings Accm.Depr.	135609	2022-09-20 08:39:05.264448+00	2022-09-20 08:39:05.264533+00	1	t	\N	f	f
320	CATEGORY	Category	Machinery & Equipment	135610	2022-09-20 08:39:05.264741+00	2022-09-20 08:39:05.264836+00	1	t	\N	f	f
321	CATEGORY	Category	Machinery & Equipment Accm.Depr.	135611	2022-09-20 08:39:05.265052+00	2022-09-20 08:39:05.265075+00	1	t	\N	f	f
322	CATEGORY	Category	Snacks	135447	2022-09-20 08:39:05.265125+00	2022-09-20 08:39:05.265146+00	1	t	\N	f	f
323	CATEGORY	Category	Utility	135449	2022-09-20 08:39:05.265236+00	2022-09-20 08:39:05.265266+00	1	t	\N	f	f
324	CATEGORY	Category	Others	135451	2022-09-20 08:39:05.265329+00	2022-09-20 08:39:05.265356+00	1	t	\N	f	f
326	CATEGORY	Category	Bus	135455	2022-09-20 08:39:05.26577+00	2022-09-20 08:39:05.265841+00	1	t	\N	f	f
328	CATEGORY	Category	Courier	135458	2022-09-20 08:39:05.276799+00	2022-09-20 08:39:05.27723+00	1	t	\N	f	f
329	CATEGORY	Category	Hotel	135459	2022-09-20 08:39:05.27731+00	2022-09-20 08:39:05.277332+00	1	t	\N	f	f
330	CATEGORY	Category	Professional Services	135460	2022-09-20 08:39:05.277386+00	2022-09-20 08:39:05.277406+00	1	t	\N	f	f
331	CATEGORY	Category	Phone	135461	2022-09-20 08:39:05.277459+00	2022-09-20 08:39:05.279024+00	1	t	\N	f	f
332	CATEGORY	Category	Travel Expenses which supports National - International	135542	2022-09-20 08:39:05.279713+00	2022-09-20 08:39:05.279758+00	1	t	\N	f	f
333	CATEGORY	Category	Bad Debt Expense	135544	2022-09-20 08:39:05.279837+00	2022-09-20 08:39:05.279868+00	1	t	\N	f	f
327	CATEGORY	Category	Taxi	135457	2022-09-20 08:39:05.276717+00	2022-09-28 11:56:20.660976+00	1	t	\N	f	f
334	CATEGORY	Category	Travel	135545	2022-09-20 08:39:05.279951+00	2022-09-20 08:39:05.279975+00	1	t	\N	f	f
335	CATEGORY	Category	Notes Payable	135546	2022-09-20 08:39:05.280029+00	2022-09-20 08:39:05.280216+00	1	t	\N	f	f
336	CATEGORY	Category	Employee Benefits	135553	2022-09-20 08:39:05.281702+00	2022-09-20 08:39:05.281781+00	1	t	\N	f	f
337	CATEGORY	Category	Commission	135554	2022-09-20 08:39:05.281872+00	2022-09-20 08:39:05.281902+00	1	t	\N	f	f
338	CATEGORY	Category	Office Suppliesdfsd	135555	2022-09-20 08:39:05.281946+00	2022-09-20 08:39:05.281968+00	1	t	\N	f	f
339	CATEGORY	Category	COGS Services	135557	2022-09-20 08:39:05.282026+00	2022-09-20 08:39:05.282047+00	1	t	\N	f	f
340	CATEGORY	Category	COGS-Billable Hours	135558	2022-09-20 08:39:05.282109+00	2022-09-20 08:39:05.28214+00	1	t	\N	f	f
341	CATEGORY	Category	Labor Cost Variance	135559	2022-09-20 08:39:05.282205+00	2022-09-20 08:39:05.282527+00	1	t	\N	f	f
342	CATEGORY	Category	Labor Cost Offset	135560	2022-09-20 08:39:05.282922+00	2022-09-20 08:39:05.283128+00	1	t	\N	f	f
343	CATEGORY	Category	COGS-Non-Billable Hours	135561	2022-09-20 08:39:05.283983+00	2022-09-20 08:39:05.284194+00	1	t	\N	f	f
344	CATEGORY	Category	COGS-Burden on Projects	135562	2022-09-20 08:39:05.284281+00	2022-09-20 08:39:05.284312+00	1	t	\N	f	f
345	CATEGORY	Category	COGS-Overhead on Projects	135563	2022-09-20 08:39:05.284375+00	2022-09-20 08:39:05.284398+00	1	t	\N	f	f
346	CATEGORY	Category	COGS-G&A on Projects	135564	2022-09-20 08:39:05.284446+00	2022-09-20 08:39:05.284467+00	1	t	\N	f	f
347	CATEGORY	Category	COGS-Indirect projects Costs Offset	135565	2022-09-20 08:39:05.284527+00	2022-09-20 08:39:05.284557+00	1	t	\N	f	f
348	CATEGORY	Category	COGS-Reimbursed Expenses	135566	2022-09-20 08:39:05.285097+00	2022-09-20 08:39:05.285146+00	1	t	\N	f	f
349	CATEGORY	Category	COGS-Other	135569	2022-09-20 08:39:05.285212+00	2022-09-20 08:39:05.285234+00	1	t	\N	f	f
350	CATEGORY	Category	Payroll Expenses	135541	2022-09-20 08:39:05.285299+00	2022-09-20 08:39:05.285321+00	1	t	\N	f	f
351	CATEGORY	Category	Payroll Expense	135540	2022-09-20 08:39:05.285384+00	2022-09-20 08:39:05.285794+00	1	t	\N	f	f
352	CATEGORY	Category	Spot Bonus	135537	2022-09-20 08:39:05.285886+00	2022-09-20 08:39:05.286085+00	1	t	\N	f	f
353	CATEGORY	Category	Other G&A	135538	2022-09-20 08:39:05.28698+00	2022-09-20 08:39:05.287035+00	1	t	\N	f	f
354	CATEGORY	Category	Buildings	135539	2022-09-20 08:39:05.287123+00	2022-09-20 08:39:05.287151+00	1	t	\N	f	f
355	CATEGORY	Category	Dues and Expenses from Intacct	141657	2022-09-20 08:39:05.287398+00	2022-09-20 08:39:05.294211+00	1	t	\N	f	f
356	CATEGORY	Category	Supplies	145002	2022-09-20 08:39:05.294534+00	2022-09-20 08:39:05.294679+00	1	t	\N	f	f
357	CATEGORY	Category	Sync Expense Account	145003	2022-09-20 08:39:05.294753+00	2022-09-20 08:39:05.294775+00	1	t	\N	f	f
358	CATEGORY	Category	Netflix	146042	2022-09-20 08:39:05.294835+00	2022-09-20 08:39:05.294857+00	1	t	\N	f	f
359	CATEGORY	Category	Emma	146043	2022-09-20 08:39:05.294916+00	2022-09-20 08:39:05.294937+00	1	t	\N	f	f
360	CATEGORY	Category	Description about 00	137942	2022-09-20 08:39:05.294992+00	2022-09-20 08:39:05.295012+00	1	t	\N	f	f
361	CATEGORY	Category	Description about ASHWIN MANUALLY ADDED THIS	137943	2022-09-20 08:39:05.296144+00	2022-09-20 08:39:05.296218+00	1	t	\N	f	f
362	CATEGORY	Category	Description about ASHWIN MANUALLY ADDED THIS2	137944	2022-09-20 08:39:05.296307+00	2022-09-20 08:39:05.296333+00	1	t	\N	f	f
363	CATEGORY	Category	Furniture for the department	137945	2022-09-20 08:39:05.296897+00	2022-09-20 08:39:05.296936+00	1	t	\N	f	f
364	CATEGORY	Category	Equipment	137947	2022-09-20 08:39:05.297658+00	2022-09-20 08:39:05.298733+00	1	t	\N	f	f
365	CATEGORY	Category	Travel Expenses	137948	2022-09-20 08:39:05.301454+00	2022-09-20 08:39:05.301506+00	1	t	\N	f	f
367	CATEGORY	Category	WIP COGS	135931	2022-09-20 08:39:05.317972+00	2022-09-20 08:39:05.318031+00	1	t	\N	f	f
368	CATEGORY	Category	Mfg WIP	135932	2022-09-20 08:39:05.383194+00	2022-09-20 08:39:05.383226+00	1	t	\N	f	f
369	CATEGORY	Category	Purchase Price Variance	135933	2022-09-20 08:39:05.383276+00	2022-09-20 08:39:05.383298+00	1	t	\N	f	f
370	CATEGORY	Category	Build Price Variance	135934	2022-09-20 08:39:05.383694+00	2022-09-20 08:39:05.383833+00	1	t	\N	f	f
371	CATEGORY	Category	Build Quantity Variance	135935	2022-09-20 08:39:05.383901+00	2022-09-20 08:39:05.383923+00	1	t	\N	f	f
372	CATEGORY	Category	Vendor Rebates	135936	2022-09-20 08:39:05.383991+00	2022-09-20 08:39:05.384015+00	1	t	\N	f	f
373	CATEGORY	Category	Customer Return Variance	135937	2022-09-20 08:39:05.384065+00	2022-09-20 08:39:05.384087+00	1	t	\N	f	f
374	CATEGORY	Category	Vendor Return Variance	135938	2022-09-20 08:39:05.38415+00	2022-09-20 08:39:05.384178+00	1	t	\N	f	f
375	CATEGORY	Category	Mfg Scrap	135939	2022-09-20 08:39:05.38423+00	2022-09-20 08:39:05.384711+00	1	t	\N	f	f
376	CATEGORY	Category	Manufacturing Expenses	135940	2022-09-20 08:39:05.384854+00	2022-09-20 08:39:05.384939+00	1	t	\N	f	f
377	CATEGORY	Category	Labor	135941	2022-09-20 08:39:05.385003+00	2022-09-20 08:39:05.385024+00	1	t	\N	f	f
378	CATEGORY	Category	Labor Burden	135942	2022-09-20 08:39:05.385086+00	2022-09-20 08:39:05.385106+00	1	t	\N	f	f
379	CATEGORY	Category	Machine	135943	2022-09-20 08:39:05.385158+00	2022-09-20 08:39:05.385178+00	1	t	\N	f	f
380	CATEGORY	Category	Machine Burden	135944	2022-09-20 08:39:05.385231+00	2022-09-20 08:39:05.385252+00	1	t	\N	f	f
381	CATEGORY	Category	WIP Variance	135945	2022-09-20 08:39:05.385301+00	2022-09-20 08:39:05.385312+00	1	t	\N	f	f
382	CATEGORY	Category	ash	135946	2022-09-20 08:39:05.385355+00	2022-09-20 08:39:05.385375+00	1	t	\N	f	f
383	CATEGORY	Category	sub ash	135947	2022-09-20 08:39:05.385436+00	2022-09-20 08:39:05.385456+00	1	t	\N	f	f
384	CATEGORY	Category	Undeposited Funds	135868	2022-09-20 08:39:05.385506+00	2022-09-20 08:39:05.385516+00	1	t	\N	f	f
385	CATEGORY	Category	Other Receivables	135870	2022-09-20 08:39:05.385567+00	2022-09-20 08:39:05.385588+00	1	t	\N	f	f
386	CATEGORY	Category	Bill Exchange Rate Variance	135923	2022-09-20 08:39:05.385639+00	2022-09-20 08:39:05.38566+00	1	t	\N	f	f
387	CATEGORY	Category	Inventory Transfer Price Gain - Loss	135924	2022-09-20 08:39:05.385721+00	2022-09-20 08:39:05.385741+00	1	t	\N	f	f
388	CATEGORY	Category	Unbuild Variance	135925	2022-09-20 08:39:05.385791+00	2022-09-20 08:39:05.385812+00	1	t	\N	f	f
389	CATEGORY	Category	Rounding Gain-Loss	135926	2022-09-20 08:39:05.385872+00	2022-09-20 08:39:05.385892+00	1	t	\N	f	f
390	CATEGORY	Category	Realized Gain-Loss	135927	2022-09-20 08:39:05.385943+00	2022-09-20 08:39:05.385964+00	1	t	\N	f	f
391	CATEGORY	Category	Unrealized Gain-Loss	135928	2022-09-20 08:39:05.386024+00	2022-09-20 08:39:05.386045+00	1	t	\N	f	f
392	CATEGORY	Category	WIP	135929	2022-09-20 08:39:05.386095+00	2022-09-20 08:39:05.386105+00	1	t	\N	f	f
393	CATEGORY	Category	WIP Revenue	135930	2022-09-20 08:39:05.391399+00	2022-09-20 08:39:05.391464+00	1	t	\N	f	f
394	CATEGORY	Category	Integration Test Account	135794	2022-09-20 08:39:05.391628+00	2022-09-20 08:39:05.391679+00	1	t	\N	f	f
395	CATEGORY	Category	Travelling Charges	135795	2022-09-20 08:39:05.392393+00	2022-09-20 08:39:05.392471+00	1	t	\N	f	f
396	CATEGORY	Category	expense category	135797	2022-09-20 08:39:05.39286+00	2022-09-20 08:39:05.392929+00	1	t	\N	f	f
397	CATEGORY	Category	Cellular Phone	135792	2022-09-20 08:39:05.393+00	2022-09-20 08:39:05.393021+00	1	t	\N	f	f
398	CATEGORY	Category	Meals & Entertainment	135793	2022-09-20 08:39:05.393082+00	2022-09-20 08:39:05.393103+00	1	t	\N	f	f
399	CATEGORY	Category	Allowance For Doubtful Accounts	135570	2022-09-20 08:39:05.393164+00	2022-09-20 08:39:05.393184+00	1	t	\N	f	f
400	CATEGORY	Category	Office Supplies 2	135744	2022-09-20 08:39:05.393236+00	2022-09-20 08:39:05.393257+00	1	t	\N	f	f
401	CATEGORY	Category	Common Stock	135631	2022-09-20 08:39:05.393307+00	2022-09-20 08:39:05.393328+00	1	t	\N	f	f
402	CATEGORY	Category	Preferred Stock	135632	2022-09-20 08:39:05.393379+00	2022-09-20 08:39:05.393399+00	1	t	\N	f	f
403	CATEGORY	Category	Retained Earnings	135633	2022-09-20 08:39:05.39346+00	2022-09-20 08:39:05.39348+00	1	t	\N	f	f
404	CATEGORY	Category	COGS Sales	135634	2022-09-20 08:39:05.393529+00	2022-09-20 08:39:05.39354+00	1	t	\N	f	f
405	CATEGORY	Category	SVB Checking 3	135600	2022-09-20 08:39:05.39358+00	2022-09-20 08:39:05.393601+00	1	t	\N	f	f
406	CATEGORY	Category	Activity	135444	2022-09-20 08:39:05.393651+00	2022-09-20 08:39:05.393672+00	1	t	\N	f	f
407	CATEGORY	Category	Train	135445	2022-09-20 08:39:05.393732+00	2022-09-20 08:39:05.393753+00	1	t	\N	f	f
408	CATEGORY	Category	Allocations	135549	2022-09-20 08:39:05.393805+00	2022-09-20 08:39:05.393825+00	1	t	\N	f	f
409	CATEGORY	Category	Patents & Licenses	135552	2022-09-20 08:39:05.393874+00	2022-09-20 08:39:05.393885+00	1	t	\N	f	f
410	CATEGORY	Category	Accumulated OCI	135547	2022-09-20 08:39:05.393925+00	2022-09-20 08:39:05.393946+00	1	t	\N	f	f
411	CATEGORY	Category	Goods in Transit	135548	2022-09-20 08:39:05.394006+00	2022-09-20 08:39:05.394026+00	1	t	\N	f	f
412	CATEGORY	Category	UI777ZUG5P / Turbo charged	191853	2022-09-20 08:39:05.394076+00	2022-09-20 08:39:05.394097+00	1	t	\N	f	f
413	CATEGORY	Category	747DS1JYZB / Turbo charged	191852	2022-09-20 08:39:05.394157+00	2022-09-20 08:39:05.394177+00	1	t	\N	f	f
414	CATEGORY	Category	C72U5RL80N / Turbo charged	191851	2022-09-20 08:39:05.39422+00	2022-09-20 08:39:05.39424+00	1	t	\N	f	f
415	CATEGORY	Category	BNDNQCGL2A / Turbo charged	191850	2022-09-20 08:39:05.394301+00	2022-09-20 08:39:05.394322+00	1	t	\N	f	f
416	CATEGORY	Category	R6KJ5YA4U9 / Turbo charged	191848	2022-09-20 08:39:05.394374+00	2022-09-20 08:39:05.394746+00	1	t	\N	f	f
417	CATEGORY	Category	D1IO8OGBJ7 / Turbo charged	191847	2022-09-20 08:39:05.394814+00	2022-09-20 08:39:05.394843+00	1	t	\N	f	f
418	CATEGORY	Category	XEC9NORGDY / Turbo charged	191846	2022-09-20 08:39:05.952614+00	2022-09-20 08:39:05.952721+00	1	t	\N	f	f
419	CATEGORY	Category	DWK2H94RM7 / Turbo charged	191845	2022-09-20 08:39:05.952995+00	2022-09-20 08:39:05.953033+00	1	t	\N	f	f
420	CATEGORY	Category	IZJZZ3S9E7 / Turbo charged	191844	2022-09-20 08:39:05.953124+00	2022-09-20 08:39:05.953718+00	1	t	\N	f	f
421	CATEGORY	Category	0215IGBNYP / Turbo charged	191842	2022-09-20 08:39:05.954232+00	2022-09-20 08:39:05.954605+00	1	t	\N	f	f
422	CATEGORY	Category	1SBDCCFM3Q / Turbo charged	191841	2022-09-20 08:39:05.961483+00	2022-09-20 08:39:05.961526+00	1	t	\N	f	f
423	CATEGORY	Category	EOHGT9QJO4 / Turbo charged	191840	2022-09-20 08:39:05.961594+00	2022-09-20 08:39:05.961624+00	1	t	\N	f	f
424	CATEGORY	Category	NXPD1U8GHJ / Turbo charged	191813	2022-09-20 08:39:05.96169+00	2022-09-20 08:39:05.961722+00	1	t	\N	f	f
425	CATEGORY	Category	27Z4X2C201 / Turbo charged	191812	2022-09-20 08:39:05.963735+00	2022-09-20 08:39:05.963799+00	1	t	\N	f	f
426	CATEGORY	Category	CDGMCX2GYA / Turbo charged	191811	2022-09-20 08:39:05.965777+00	2022-09-20 08:39:05.965829+00	1	t	\N	f	f
427	CATEGORY	Category	JVFYUUP52V / Turbo charged	191810	2022-09-20 08:39:05.967202+00	2022-09-20 08:39:05.967358+00	1	t	\N	f	f
428	CATEGORY	Category	GG10QAP2S5 / Turbo charged	191809	2022-09-20 08:39:05.967575+00	2022-09-20 08:39:05.967614+00	1	t	\N	f	f
429	CATEGORY	Category	AAHWZOY5QZ / Turbo charged	191808	2022-09-20 08:39:05.967872+00	2022-09-20 08:39:05.967906+00	1	t	\N	f	f
430	CATEGORY	Category	6QLNH6Y4UM / Turbo charged	191807	2022-09-20 08:39:05.967967+00	2022-09-20 08:39:05.967988+00	1	t	\N	f	f
431	CATEGORY	Category	RHTSGJD4CV / Turbo charged	191806	2022-09-20 08:39:05.96804+00	2022-09-20 08:39:05.968053+00	1	t	\N	f	f
432	CATEGORY	Category	W6RV83BFWU / Turbo charged	191805	2022-09-20 08:39:05.968622+00	2022-09-20 08:39:05.968711+00	1	t	\N	f	f
433	CATEGORY	Category	ZIZU1AAHLF / Turbo charged	191804	2022-09-20 08:39:05.968836+00	2022-09-20 08:39:05.968877+00	1	t	\N	f	f
434	CATEGORY	Category	WRVEPSQLUO / Turbo charged	191803	2022-09-20 08:39:05.970364+00	2022-09-20 08:39:05.971616+00	1	t	\N	f	f
435	CATEGORY	Category	G5HSJNY9V8 / Turbo charged	191802	2022-09-20 08:39:05.973651+00	2022-09-20 08:39:05.973711+00	1	t	\N	f	f
436	CATEGORY	Category	FDU2ZPCGV4 / Turbo charged	191801	2022-09-20 08:39:05.975713+00	2022-09-20 08:39:05.97575+00	1	t	\N	f	f
437	CATEGORY	Category	Q230CP6HS8 / Turbo charged	191800	2022-09-20 08:39:05.975816+00	2022-09-20 08:39:05.975847+00	1	t	\N	f	f
438	CATEGORY	Category	SVWPR6H082 / Turbo charged	191799	2022-09-20 08:39:05.976067+00	2022-09-20 08:39:05.976101+00	1	t	\N	f	f
439	CATEGORY	Category	49BVB05MSS / Turbo charged	191798	2022-09-20 08:39:05.976165+00	2022-09-20 08:39:05.976194+00	1	t	\N	f	f
440	CATEGORY	Category	T5AOOEOIMJ / Turbo charged	191797	2022-09-20 08:39:05.976256+00	2022-09-20 08:39:05.976286+00	1	t	\N	f	f
441	CATEGORY	Category	03QBRUQL9Y / Turbo charged	191796	2022-09-20 08:39:05.976348+00	2022-09-20 08:39:05.976377+00	1	t	\N	f	f
442	CATEGORY	Category	MTD7QH6N7D / Turbo charged	191795	2022-09-20 08:39:05.976457+00	2022-09-20 08:39:05.980467+00	1	t	\N	f	f
443	CATEGORY	Category	RGUG2EU1X7 / Turbo charged	191794	2022-09-20 08:39:05.9806+00	2022-09-20 08:39:05.98062+00	1	t	\N	f	f
444	CATEGORY	Category	5JHCVQD5SS / Turbo charged	191793	2022-09-20 08:39:05.980675+00	2022-09-20 08:39:05.980706+00	1	t	\N	f	f
445	CATEGORY	Category	YO63CHLCBF / Turbo charged	191792	2022-09-20 08:39:05.980758+00	2022-09-20 08:39:05.980779+00	1	t	\N	f	f
446	CATEGORY	Category	2CSL18LRX5 / Turbo charged	191791	2022-09-20 08:39:05.980841+00	2022-09-20 08:39:05.980873+00	1	t	\N	f	f
447	CATEGORY	Category	LQEK36KCCF / Turbo charged	191790	2022-09-20 08:39:05.981057+00	2022-09-20 08:39:05.981435+00	1	t	\N	f	f
448	CATEGORY	Category	OT0WPR3LG1 / Turbo charged	191789	2022-09-20 08:39:05.981667+00	2022-09-20 08:39:05.981698+00	1	t	\N	f	f
449	CATEGORY	Category	YG9ZHOW03L / Turbo charged	191788	2022-09-20 08:39:05.981762+00	2022-09-20 08:39:05.981792+00	1	t	\N	f	f
450	CATEGORY	Category	9Q25F572X1 / Turbo charged	191787	2022-09-20 08:39:05.982043+00	2022-09-20 08:39:05.982077+00	1	t	\N	f	f
451	CATEGORY	Category	XNJ6IYQTT6 / Turbo charged	191786	2022-09-20 08:39:05.982142+00	2022-09-20 08:39:05.983429+00	1	t	\N	f	f
452	CATEGORY	Category	EGJMQFKSKM / Turbo charged	191785	2022-09-20 08:39:06.001358+00	2022-09-20 08:39:06.001407+00	1	t	\N	f	f
453	CATEGORY	Category	T1WP4WBELF / Turbo charged	191784	2022-09-20 08:39:06.001607+00	2022-09-20 08:39:06.001696+00	1	t	\N	f	f
454	CATEGORY	Category	MAUZTC2I53 / Turbo charged	191783	2022-09-20 08:39:06.001833+00	2022-09-20 08:39:06.00186+00	1	t	\N	f	f
455	CATEGORY	Category	TG1OG645TP / Turbo charged	191782	2022-09-20 08:39:06.001957+00	2022-09-20 08:39:06.002009+00	1	t	\N	f	f
456	CATEGORY	Category	X4R0A458J3 / Turbo charged	191781	2022-09-20 08:39:06.00257+00	2022-09-20 08:39:06.002617+00	1	t	\N	f	f
457	CATEGORY	Category	OUR0YT9KBK / Turbo charged	191780	2022-09-20 08:39:06.002692+00	2022-09-20 08:39:06.002763+00	1	t	\N	f	f
458	CATEGORY	Category	F0YGCWO5PP / Turbo charged	191779	2022-09-20 08:39:06.002978+00	2022-09-20 08:39:06.003013+00	1	t	\N	f	f
459	CATEGORY	Category	USD4J624GO / Turbo charged	191778	2022-09-20 08:39:06.003154+00	2022-09-20 08:39:06.003359+00	1	t	\N	f	f
460	CATEGORY	Category	0UDWEKF5QQ / Turbo charged	191777	2022-09-20 08:39:06.003448+00	2022-09-20 08:39:06.003472+00	1	t	\N	f	f
461	CATEGORY	Category	JQTAKMBYNJ / Turbo charged	191776	2022-09-20 08:39:06.003548+00	2022-09-20 08:39:06.003622+00	1	t	\N	f	f
462	CATEGORY	Category	1NIPCD4AIV / Turbo charged	191775	2022-09-20 08:39:06.004412+00	2022-09-20 08:39:06.004479+00	1	t	\N	f	f
463	CATEGORY	Category	95FDDT0ADR / Turbo charged	191774	2022-09-20 08:39:06.004746+00	2022-09-20 08:39:06.004778+00	1	t	\N	f	f
464	CATEGORY	Category	LW8V0C86U9 / Turbo charged	191773	2022-09-20 08:39:06.004843+00	2022-09-20 08:39:06.004864+00	1	t	\N	f	f
465	CATEGORY	Category	SBNNYXHGJM / Turbo charged	191772	2022-09-20 08:39:06.004925+00	2022-09-20 08:39:06.004946+00	1	t	\N	f	f
466	CATEGORY	Category	OEZ61NIBGN / Turbo charged	191771	2022-09-20 08:39:06.005035+00	2022-09-20 08:39:06.005084+00	1	t	\N	f	f
467	CATEGORY	Category	YA65ILOGVV / Turbo charged	191770	2022-09-20 08:39:06.005417+00	2022-09-20 08:39:06.005451+00	1	t	\N	f	f
468	CATEGORY	Category	Z9EDD2VZC3 / Turbo charged	191769	2022-09-20 08:39:06.054787+00	2022-09-20 08:39:06.054841+00	1	t	\N	f	f
469	CATEGORY	Category	I4XUSD23KB / Turbo charged	191768	2022-09-20 08:39:06.055069+00	2022-09-20 08:39:06.055192+00	1	t	\N	f	f
470	CATEGORY	Category	PNSOA0VKSF / Turbo charged	191767	2022-09-20 08:39:06.055481+00	2022-09-20 08:39:06.055515+00	1	t	\N	f	f
471	CATEGORY	Category	RBJU6PV6UZ / Turbo charged	191766	2022-09-20 08:39:06.055593+00	2022-09-20 08:39:06.055627+00	1	t	\N	f	f
472	CATEGORY	Category	PO4UXUPB2Z / Turbo charged	191765	2022-09-20 08:39:06.055812+00	2022-09-20 08:39:06.055901+00	1	t	\N	f	f
473	CATEGORY	Category	DM7138IDE2 / Turbo charged	191764	2022-09-20 08:39:06.056048+00	2022-09-20 08:39:06.056085+00	1	t	\N	f	f
474	CATEGORY	Category	PMNG0N8KSZ / Turbo charged	191763	2022-09-20 08:39:06.056207+00	2022-09-20 08:39:06.056251+00	1	t	\N	f	f
475	CATEGORY	Category	36TEBIWA0N / Turbo charged	191762	2022-09-20 08:39:06.056399+00	2022-09-20 08:39:06.056446+00	1	t	\N	f	f
476	CATEGORY	Category	GWNYCAUI7U / Turbo charged	191761	2022-09-20 08:39:06.05654+00	2022-09-20 08:39:06.056589+00	1	t	\N	f	f
477	CATEGORY	Category	XBBEZH9O4N / Turbo charged	191760	2022-09-20 08:39:06.057215+00	2022-09-20 08:39:06.058558+00	1	t	\N	f	f
478	CATEGORY	Category	HBKP7A0DNR / Turbo charged	191759	2022-09-20 08:39:06.059893+00	2022-09-20 08:39:06.059969+00	1	t	\N	f	f
479	CATEGORY	Category	7ZAAQDCQQN / Turbo charged	191758	2022-09-20 08:39:06.060193+00	2022-09-20 08:39:06.060452+00	1	t	\N	f	f
480	CATEGORY	Category	5DNCP094R0 / Turbo charged	191757	2022-09-20 08:39:06.060697+00	2022-09-20 08:39:06.060734+00	1	t	\N	f	f
481	CATEGORY	Category	LCU8INQONN / Turbo charged	191756	2022-09-20 08:39:06.060832+00	2022-09-20 08:39:06.060879+00	1	t	\N	f	f
482	CATEGORY	Category	DWU8MKBQEV / Turbo charged	191755	2022-09-20 08:39:06.060977+00	2022-09-20 08:39:06.061017+00	1	t	\N	f	f
483	CATEGORY	Category	O020KR52QV / Turbo charged	191754	2022-09-20 08:39:06.061109+00	2022-09-20 08:39:06.061146+00	1	t	\N	f	f
484	CATEGORY	Category	SNB8I4896F / Turbo charged	191753	2022-09-20 08:39:06.061225+00	2022-09-20 08:39:06.061259+00	1	t	\N	f	f
485	CATEGORY	Category	ZSGKDU3OLB / Turbo charged	191752	2022-09-20 08:39:06.061334+00	2022-09-20 08:39:06.06136+00	1	t	\N	f	f
486	CATEGORY	Category	XN7QJZBTGW / Turbo charged	191751	2022-09-20 08:39:06.06143+00	2022-09-20 08:39:06.061459+00	1	t	\N	f	f
487	CATEGORY	Category	Q17J4DV6PY / Turbo charged	191750	2022-09-20 08:39:06.061548+00	2022-09-20 08:39:06.061587+00	1	t	\N	f	f
488	CATEGORY	Category	VEU3R97JU6 / Turbo charged	191749	2022-09-20 08:39:06.06206+00	2022-09-20 08:39:06.062659+00	1	t	\N	f	f
489	CATEGORY	Category	H4FLZPRDRU / Turbo charged	191748	2022-09-20 08:39:06.062769+00	2022-09-20 08:39:06.0628+00	1	t	\N	f	f
490	CATEGORY	Category	MQ3MHKG1JM / Turbo charged	191747	2022-09-20 08:39:06.062852+00	2022-09-20 08:39:06.062872+00	1	t	\N	f	f
491	CATEGORY	Category	OPUXX1NWJD / Turbo charged	191746	2022-09-20 08:39:06.062913+00	2022-09-20 08:39:06.062935+00	1	t	\N	f	f
492	CATEGORY	Category	XZXC2AN5UM / Turbo charged	191745	2022-09-20 08:39:06.063156+00	2022-09-20 08:39:06.063333+00	1	t	\N	f	f
493	CATEGORY	Category	9GO0WXN6RN / Turbo charged	191744	2022-09-20 08:39:06.063648+00	2022-09-20 08:39:06.063694+00	1	t	\N	f	f
494	CATEGORY	Category	FYW3N2Z4G1 / Turbo charged	191743	2022-09-20 08:39:06.064358+00	2022-09-20 08:39:06.064406+00	1	t	\N	f	f
495	CATEGORY	Category	M0P4RTHRRA / Turbo charged	191742	2022-09-20 08:39:06.064615+00	2022-09-20 08:39:06.064667+00	1	t	\N	f	f
496	CATEGORY	Category	M8MES6DZKB / Turbo charged	191741	2022-09-20 08:39:06.064748+00	2022-09-20 08:39:06.064911+00	1	t	\N	f	f
497	CATEGORY	Category	2WN3XRLS6H / Turbo charged	191740	2022-09-20 08:39:06.065064+00	2022-09-20 08:39:06.06509+00	1	t	\N	f	f
498	CATEGORY	Category	8RJGQU3LBA / Turbo charged	191739	2022-09-20 08:39:06.065159+00	2022-09-20 08:39:06.065789+00	1	t	\N	f	f
499	CATEGORY	Category	6RTQSGGVBB / Turbo charged	191738	2022-09-20 08:39:06.066294+00	2022-09-20 08:39:06.066939+00	1	t	\N	f	f
500	CATEGORY	Category	71DTN3JPS4 / Turbo charged	191737	2022-09-20 08:39:06.067156+00	2022-09-20 08:39:06.067313+00	1	t	\N	f	f
501	CATEGORY	Category	QE0PQSDQPB / Turbo charged	191736	2022-09-20 08:39:06.069064+00	2022-09-20 08:39:06.069117+00	1	t	\N	f	f
502	CATEGORY	Category	CD5C1P0EBC / Turbo charged	191735	2022-09-20 08:39:06.069189+00	2022-09-20 08:39:06.069219+00	1	t	\N	f	f
503	CATEGORY	Category	4CF762Q721 / Turbo charged	191734	2022-09-20 08:39:06.069296+00	2022-09-20 08:39:06.069326+00	1	t	\N	f	f
504	CATEGORY	Category	62WRSSZKV3 / Turbo charged	191733	2022-09-20 08:39:06.069389+00	2022-09-20 08:39:06.069418+00	1	t	\N	f	f
505	CATEGORY	Category	XNNLG4CWVK / Turbo charged	191732	2022-09-20 08:39:06.06948+00	2022-09-20 08:39:06.069508+00	1	t	\N	f	f
506	CATEGORY	Category	6HEKYZATT2 / Turbo charged	191731	2022-09-20 08:39:06.06957+00	2022-09-20 08:39:06.069599+00	1	t	\N	f	f
507	CATEGORY	Category	9SI9Y9A036 / Turbo charged	191730	2022-09-20 08:39:06.06966+00	2022-09-20 08:39:06.069689+00	1	t	\N	f	f
508	CATEGORY	Category	D1A81KCH82 / Turbo charged	191728	2022-09-20 08:39:06.069751+00	2022-09-20 08:39:06.069782+00	1	t	\N	f	f
509	CATEGORY	Category	5VD52OUE8G / Turbo charged	191727	2022-09-20 08:39:06.069847+00	2022-09-20 08:39:06.070045+00	1	t	\N	f	f
510	CATEGORY	Category	RMLZWIV6W7 / Turbo charged	191726	2022-09-20 08:39:06.070187+00	2022-09-20 08:39:06.070428+00	1	t	\N	f	f
511	CATEGORY	Category	Z07A9NN1DM / Turbo charged	191694	2022-09-20 08:39:06.071579+00	2022-09-20 08:39:06.072185+00	1	t	\N	f	f
512	CATEGORY	Category	XG2FEN961D / Turbo charged	191693	2022-09-20 08:39:06.074397+00	2022-09-20 08:39:06.075535+00	1	t	\N	f	f
513	CATEGORY	Category	ZDM9M85NEK / Turbo charged	191692	2022-09-20 08:39:06.07588+00	2022-09-20 08:39:06.075961+00	1	t	\N	f	f
514	CATEGORY	Category	55D90KR22F / Turbo charged	191691	2022-09-20 08:39:06.076113+00	2022-09-20 08:39:06.076173+00	1	t	\N	f	f
515	CATEGORY	Category	69W9JMEXIP / Turbo charged	191690	2022-09-20 08:39:06.076314+00	2022-09-20 08:39:06.076783+00	1	t	\N	f	f
516	CATEGORY	Category	UTJEMXABWZ / Turbo charged	191689	2022-09-20 08:39:06.079092+00	2022-09-20 08:39:06.091651+00	1	t	\N	f	f
517	CATEGORY	Category	1KPDKITYMO / Turbo charged	191688	2022-09-20 08:39:06.092465+00	2022-09-20 08:39:06.092563+00	1	t	\N	f	f
518	CATEGORY	Category	09ZKNVZ4O6 / Turbo charged	191687	2022-09-20 08:39:06.124978+00	2022-09-20 08:39:06.125146+00	1	t	\N	f	f
519	CATEGORY	Category	RYHQGEPACZ / Turbo charged	191686	2022-09-20 08:39:06.125571+00	2022-09-20 08:39:06.125602+00	1	t	\N	f	f
520	CATEGORY	Category	OYSLBGDVDT / Turbo charged	191685	2022-09-20 08:39:06.125926+00	2022-09-20 08:39:06.126788+00	1	t	\N	f	f
521	CATEGORY	Category	KF5LT1RF09 / Turbo charged	191684	2022-09-20 08:39:06.126892+00	2022-09-20 08:39:06.126924+00	1	t	\N	f	f
522	CATEGORY	Category	SKJX43FH5L / Turbo charged	191683	2022-09-20 08:39:06.127896+00	2022-09-20 08:39:06.127932+00	1	t	\N	f	f
523	CATEGORY	Category	JHLK63ZZWB / Turbo charged	191682	2022-09-20 08:39:06.128028+00	2022-09-20 08:39:06.128058+00	1	t	\N	f	f
524	CATEGORY	Category	V1EJ6D8VGJ / Turbo charged	191680	2022-09-20 08:39:06.128118+00	2022-09-20 08:39:06.128137+00	1	t	\N	f	f
525	CATEGORY	Category	AVXYHDXGHR / Turbo charged	191679	2022-09-20 08:39:06.128185+00	2022-09-20 08:39:06.129634+00	1	t	\N	f	f
526	CATEGORY	Category	560RKMO5QW / Turbo charged	191678	2022-09-20 08:39:06.129897+00	2022-09-20 08:39:06.129935+00	1	t	\N	f	f
527	CATEGORY	Category	IVX8Q7M4OL / Turbo charged	191677	2022-09-20 08:39:06.130009+00	2022-09-20 08:39:06.130039+00	1	t	\N	f	f
528	CATEGORY	Category	JVRYCPUK0F / Turbo charged	191676	2022-09-20 08:39:06.130133+00	2022-09-20 08:39:06.130162+00	1	t	\N	f	f
529	CATEGORY	Category	DSA93VPG9K / Turbo charged	191675	2022-09-20 08:39:06.131942+00	2022-09-20 08:39:06.132031+00	1	t	\N	f	f
530	CATEGORY	Category	RGLB5QES1M / Turbo charged	191674	2022-09-20 08:39:06.132423+00	2022-09-20 08:39:06.13248+00	1	t	\N	f	f
531	CATEGORY	Category	BEOCQYS8EN / Turbo charged	191672	2022-09-20 08:39:06.132595+00	2022-09-20 08:39:06.132624+00	1	t	\N	f	f
532	CATEGORY	Category	QYQKO8SPR6 / Turbo charged	191671	2022-09-20 08:39:06.132681+00	2022-09-20 08:39:06.132703+00	1	t	\N	f	f
533	CATEGORY	Category	WFRIUTX9C7 / Turbo charged	191669	2022-09-20 08:39:06.133666+00	2022-09-20 08:39:06.133721+00	1	t	\N	f	f
534	CATEGORY	Category	D47UDLB4F8 / Turbo charged	191667	2022-09-20 08:39:06.133781+00	2022-09-20 08:39:06.133812+00	1	t	\N	f	f
535	CATEGORY	Category	IKIJX0TM8Y / Turbo charged	191666	2022-09-20 08:39:06.133892+00	2022-09-20 08:39:06.133916+00	1	t	\N	f	f
536	CATEGORY	Category	1A8A84WBA2 / Turbo charged	191665	2022-09-20 08:39:06.133973+00	2022-09-20 08:39:06.133994+00	1	t	\N	f	f
537	CATEGORY	Category	69NR7TNK5P / Turbo charged	191664	2022-09-20 08:39:06.135337+00	2022-09-20 08:39:06.135392+00	1	t	\N	f	f
538	CATEGORY	Category	RCYUA4VYHK / Turbo charged	191663	2022-09-20 08:39:06.135474+00	2022-09-20 08:39:06.135496+00	1	t	\N	f	f
539	CATEGORY	Category	H1979NVX85 / Turbo charged	191662	2022-09-20 08:39:06.135559+00	2022-09-20 08:39:06.13559+00	1	t	\N	f	f
540	CATEGORY	Category	OEAN2S0661 / Turbo charged	191661	2022-09-20 08:39:06.135651+00	2022-09-20 08:39:06.135663+00	1	t	\N	f	f
541	CATEGORY	Category	8ZUVNA95N1 / Turbo charged	191631	2022-09-20 08:39:06.135714+00	2022-09-20 08:39:06.13575+00	1	t	\N	f	f
542	CATEGORY	Category	GLBTYBKH0W / Turbo charged	191630	2022-09-20 08:39:06.135812+00	2022-09-20 08:39:06.135832+00	1	t	\N	f	f
543	CATEGORY	Category	T2PVG1SAHV / Turbo charged	191627	2022-09-20 08:39:06.135885+00	2022-09-20 08:39:06.135932+00	1	t	\N	f	f
544	CATEGORY	Category	II6NWV8PK4 / Turbo charged	191626	2022-09-20 08:39:06.135981+00	2022-09-20 08:39:06.136002+00	1	t	\N	f	f
545	CATEGORY	Category	R92514U6N6 / Turbo charged	191625	2022-09-20 08:39:06.136063+00	2022-09-20 08:39:06.136092+00	1	t	\N	f	f
546	CATEGORY	Category	Y7ALNUN1XP / Turbo charged	191624	2022-09-20 08:39:06.136604+00	2022-09-20 08:39:06.138926+00	1	t	\N	f	f
547	CATEGORY	Category	HTR8W6D3JR / Turbo charged	191623	2022-09-20 08:39:06.139133+00	2022-09-20 08:39:06.139207+00	1	t	\N	f	f
548	CATEGORY	Category	DEL4M6NRFW / Turbo charged	191622	2022-09-20 08:39:06.141256+00	2022-09-20 08:39:06.141302+00	1	t	\N	f	f
549	CATEGORY	Category	QVOZSLTNXZ / Turbo charged	191621	2022-09-20 08:39:06.141616+00	2022-09-20 08:39:06.141648+00	1	t	\N	f	f
550	CATEGORY	Category	Nilesh Pant 112 / Turbo charged	191614	2022-09-20 08:39:06.145256+00	2022-09-20 08:39:06.145424+00	1	t	\N	f	f
551	CATEGORY	Category	s;dhfsodhiyfowiehrwoiehrowiehrowiehr / Turbo charged	191578	2022-09-20 08:39:06.145488+00	2022-09-20 08:39:06.145519+00	1	t	\N	f	f
552	CATEGORY	Category	LF3OR9B6UY / Turbo charged	191229	2022-09-20 08:39:06.145578+00	2022-09-20 08:39:06.145591+00	1	t	\N	f	f
553	CATEGORY	Category	3GYAQ1QYHQ / Turbo charged	191228	2022-09-20 08:39:06.145662+00	2022-09-20 08:39:06.145693+00	1	t	\N	f	f
554	CATEGORY	Category	PVDGPPF2SC / Turbo charged	191158	2022-09-20 08:39:06.147223+00	2022-09-20 08:39:06.147261+00	1	t	\N	f	f
555	CATEGORY	Category	KOY9ZL06FA / Turbo charged	191157	2022-09-20 08:39:06.148508+00	2022-09-20 08:39:06.148564+00	1	t	\N	f	f
556	CATEGORY	Category	WSTNCJ6Q5H / Turbo charged	191156	2022-09-20 08:39:06.148619+00	2022-09-20 08:39:06.14864+00	1	t	\N	f	f
557	CATEGORY	Category	NVV6A35DEB / Turbo charged	191155	2022-09-20 08:39:06.148696+00	2022-09-20 08:39:06.148717+00	1	t	\N	f	f
558	CATEGORY	Category	Z90LGUXCKD / Turbo charged	191154	2022-09-20 08:39:06.148778+00	2022-09-20 08:39:06.148828+00	1	t	\N	f	f
559	CATEGORY	Category	13GI6S3UYN / Turbo charged	191153	2022-09-20 08:39:06.149605+00	2022-09-20 08:39:06.149643+00	1	t	\N	f	f
560	CATEGORY	Category	WQAYU3EVN9 / Turbo charged	191152	2022-09-20 08:39:06.149743+00	2022-09-20 08:39:06.149764+00	1	t	\N	f	f
561	CATEGORY	Category	GHFPC90RHT / Turbo charged	191151	2022-09-20 08:39:06.149818+00	2022-09-20 08:39:06.14984+00	1	t	\N	f	f
562	CATEGORY	Category	M20BG0G6TW / Turbo charged	191150	2022-09-20 08:39:06.149903+00	2022-09-20 08:39:06.149933+00	1	t	\N	f	f
563	CATEGORY	Category	LTFKCOG3FH / Turbo charged	191149	2022-09-20 08:39:06.149994+00	2022-09-20 08:39:06.150046+00	1	t	\N	f	f
564	CATEGORY	Category	M08GU5OX20 / Turbo charged	191148	2022-09-20 08:39:06.150854+00	2022-09-20 08:39:06.150882+00	1	t	\N	f	f
565	CATEGORY	Category	8V1FTMOLVI / Turbo charged	191147	2022-09-20 08:39:06.150938+00	2022-09-20 08:39:06.150961+00	1	t	\N	f	f
566	CATEGORY	Category	L2CSEXHPTK / Turbo charged	191146	2022-09-20 08:39:06.151118+00	2022-09-20 08:39:06.151474+00	1	t	\N	f	f
567	CATEGORY	Category	A5QP6EJ9HR / Turbo charged	191143	2022-09-20 08:39:06.151676+00	2022-09-20 08:39:06.151716+00	1	t	\N	f	f
568	CATEGORY	Category	EY28M1P22T / Turbo charged	191142	2022-09-20 08:39:06.169973+00	2022-09-20 08:39:06.170015+00	1	t	\N	f	f
569	CATEGORY	Category	VACMTQNMYJ / Turbo charged	190103	2022-09-20 08:39:06.170082+00	2022-09-20 08:39:06.170111+00	1	t	\N	f	f
570	CATEGORY	Category	CE1SD2SQIK / Turbo charged	190102	2022-09-20 08:39:06.170173+00	2022-09-20 08:39:06.170201+00	1	t	\N	f	f
571	CATEGORY	Category	YQKG0LTOUZ / Turbo charged	189447	2022-09-20 08:39:06.17026+00	2022-09-20 08:39:06.170288+00	1	t	\N	f	f
572	CATEGORY	Category	37YWNDJGXS / Turbo charged	189446	2022-09-20 08:39:06.170347+00	2022-09-20 08:39:06.170488+00	1	t	\N	f	f
573	CATEGORY	Category	5OJBS10VAC / Turbo charged	189445	2022-09-20 08:39:06.170553+00	2022-09-20 08:39:06.17058+00	1	t	\N	f	f
574	CATEGORY	Category	248OHESQX4 / Turbo charged	189444	2022-09-20 08:39:06.170638+00	2022-09-20 08:39:06.170665+00	1	t	\N	f	f
575	CATEGORY	Category	VL45IRZHOK / Turbo charged	189443	2022-09-20 08:39:06.170722+00	2022-09-20 08:39:06.170749+00	1	t	\N	f	f
576	CATEGORY	Category	OW43OS7WUO / Turbo charged	189442	2022-09-20 08:39:06.170806+00	2022-09-20 08:39:06.170834+00	1	t	\N	f	f
577	CATEGORY	Category	QXWLZB6RGO / Turbo charged	189441	2022-09-20 08:39:06.17089+00	2022-09-20 08:39:06.170918+00	1	t	\N	f	f
578	CATEGORY	Category	LOITUJ2M1M / Turbo charged	189440	2022-09-20 08:39:06.170985+00	2022-09-20 08:39:06.171018+00	1	t	\N	f	f
579	CATEGORY	Category	QZP8MCPJI0 / Turbo charged	189439	2022-09-20 08:39:06.171088+00	2022-09-20 08:39:06.171115+00	1	t	\N	f	f
580	CATEGORY	Category	MD8XPYK2C6 / Turbo charged	189438	2022-09-20 08:39:06.171172+00	2022-09-20 08:39:06.1712+00	1	t	\N	f	f
581	CATEGORY	Category	GV18OGZEWB / Turbo charged	189437	2022-09-20 08:39:06.171257+00	2022-09-20 08:39:06.171285+00	1	t	\N	f	f
582	CATEGORY	Category	6OJKRIJ9CD / Turbo charged	189436	2022-09-20 08:39:06.171341+00	2022-09-20 08:39:06.171473+00	1	t	\N	f	f
583	CATEGORY	Category	1Q274U30JE / Turbo charged	189435	2022-09-20 08:39:06.171533+00	2022-09-20 08:39:06.171561+00	1	t	\N	f	f
584	CATEGORY	Category	DJJWB6F4HM / Turbo charged	189433	2022-09-20 08:39:06.171618+00	2022-09-20 08:39:06.171645+00	1	t	\N	f	f
585	CATEGORY	Category	VPJJOTDBCR / Turbo charged	189432	2022-09-20 08:39:06.171703+00	2022-09-20 08:39:06.17173+00	1	t	\N	f	f
586	CATEGORY	Category	L519GF6JU0 / Turbo charged	189431	2022-09-20 08:39:06.171786+00	2022-09-20 08:39:06.171813+00	1	t	\N	f	f
587	CATEGORY	Category	I3LOOW56KF / Turbo charged	189430	2022-09-20 08:39:06.17202+00	2022-09-20 08:39:06.172082+00	1	t	\N	f	f
588	CATEGORY	Category	VFDBWILTZT / Turbo charged	189429	2022-09-20 08:39:06.172153+00	2022-09-20 08:39:06.17218+00	1	t	\N	f	f
589	CATEGORY	Category	QT8T97FF18 / Turbo charged	189428	2022-09-20 08:39:06.172239+00	2022-09-20 08:39:06.172266+00	1	t	\N	f	f
590	CATEGORY	Category	ERWLSCCF5Y / Turbo charged	189427	2022-09-20 08:39:06.172323+00	2022-09-20 08:39:06.172504+00	1	t	\N	f	f
591	CATEGORY	Category	WWBU4JTK1W / Turbo charged	189398	2022-09-20 08:39:06.172621+00	2022-09-20 08:39:06.172664+00	1	t	\N	f	f
592	CATEGORY	Category	AZMVYWZ7BW / Turbo charged	189397	2022-09-20 08:39:06.17478+00	2022-09-20 08:39:06.174847+00	1	t	\N	f	f
593	CATEGORY	Category	50Q5KYEKC7 / Turbo charged	189364	2022-09-20 08:39:06.174933+00	2022-09-20 08:39:06.174962+00	1	t	\N	f	f
594	CATEGORY	Category	OZY0APPOHJ / Turbo charged	189363	2022-09-20 08:39:06.175022+00	2022-09-20 08:39:06.17505+00	1	t	\N	f	f
595	CATEGORY	Category	2VD4DE3305 / Turbo charged	189362	2022-09-20 08:39:06.175108+00	2022-09-20 08:39:06.175135+00	1	t	\N	f	f
596	CATEGORY	Category	D477IUAK5W / Turbo charged	189361	2022-09-20 08:39:06.175192+00	2022-09-20 08:39:06.175219+00	1	t	\N	f	f
597	CATEGORY	Category	AU1B8Y7TGS / Turbo charged	189357	2022-09-20 08:39:06.175275+00	2022-09-20 08:39:06.175303+00	1	t	\N	f	f
598	CATEGORY	Category	QDJ8J2CPWA / Turbo charged	189356	2022-09-20 08:39:06.175359+00	2022-09-20 08:39:06.175397+00	1	t	\N	f	f
599	CATEGORY	Category	K9ZTD8WVCG / Turbo charged	189355	2022-09-20 08:39:06.175588+00	2022-09-20 08:39:06.175616+00	1	t	\N	f	f
600	CATEGORY	Category	611ZFAT5SM / Turbo charged	188251	2022-09-20 08:39:06.175672+00	2022-09-20 08:39:06.175699+00	1	t	\N	f	f
601	CATEGORY	Category	HOUPXN0V9X / Turbo charged	185671	2022-09-20 08:39:06.175756+00	2022-09-20 08:39:06.175783+00	1	t	\N	f	f
602	CATEGORY	Category	Z8STSQH7B8 / Turbo charged	185670	2022-09-20 08:39:06.175839+00	2022-09-20 08:39:06.175908+00	1	t	\N	f	f
603	CATEGORY	Category	QHGZ8OB0QW / Turbo charged	185669	2022-09-20 08:39:06.176004+00	2022-09-20 08:39:06.176033+00	1	t	\N	f	f
604	CATEGORY	Category	PZTO6DMVX2 / Turbo charged	185622	2022-09-20 08:39:06.176092+00	2022-09-20 08:39:06.176119+00	1	t	\N	f	f
605	CATEGORY	Category	P9T0IITI3Q / Turbo charged	185621	2022-09-20 08:39:06.176175+00	2022-09-20 08:39:06.176202+00	1	t	\N	f	f
606	CATEGORY	Category	X6T4RNW4II / Turbo charged	185616	2022-09-20 08:39:06.176259+00	2022-09-20 08:39:06.176286+00	1	t	\N	f	f
607	CATEGORY	Category	UX47SL7LOE / Turbo charged	185615	2022-09-20 08:39:06.176507+00	2022-09-20 08:39:06.176548+00	1	t	\N	f	f
608	CATEGORY	Category	JDDDN0IM2E / Turbo charged	185614	2022-09-20 08:39:06.176606+00	2022-09-20 08:39:06.176633+00	1	t	\N	f	f
609	CATEGORY	Category	WGGUO7Z1SM / Turbo charged	184700	2022-09-20 08:39:06.176691+00	2022-09-20 08:39:06.176718+00	1	t	\N	f	f
610	CATEGORY	Category	ZW806W7J5F / Turbo charged	184699	2022-09-20 08:39:06.176775+00	2022-09-20 08:39:06.176802+00	1	t	\N	f	f
611	CATEGORY	Category	O4Z369SVSU / Turbo charged	184698	2022-09-20 08:39:06.17686+00	2022-09-20 08:39:06.176887+00	1	t	\N	f	f
612	CATEGORY	Category	OJ1ZB2W1AT / Turbo charged	184697	2022-09-20 08:39:06.176944+00	2022-09-20 08:39:06.176972+00	1	t	\N	f	f
613	CATEGORY	Category	IZZG6UH5Y8 / Turbo charged	184696	2022-09-20 08:39:06.177028+00	2022-09-20 08:39:06.177056+00	1	t	\N	f	f
614	CATEGORY	Category	9R407O18OU / Turbo charged	184695	2022-09-20 08:39:06.177112+00	2022-09-20 08:39:06.17714+00	1	t	\N	f	f
615	CATEGORY	Category	UATHCG2KXH / Turbo charged	184694	2022-09-20 08:39:06.177197+00	2022-09-20 08:39:06.177224+00	1	t	\N	f	f
616	CATEGORY	Category	ERLZ2WXGBY / Turbo charged	184693	2022-09-20 08:39:06.177281+00	2022-09-20 08:39:06.177309+00	1	t	\N	f	f
617	CATEGORY	Category	9GZBIA2Z9H / Turbo charged	184686	2022-09-20 08:39:06.177489+00	2022-09-20 08:39:06.17752+00	1	t	\N	f	f
618	CATEGORY	Category	JQUIDWM0VG / Turbo charged	184685	2022-09-20 08:39:06.356884+00	2022-09-20 08:39:06.356937+00	1	t	\N	f	f
619	CATEGORY	Category	CABFH8FYWJ / Turbo charged	184684	2022-09-20 08:39:06.357015+00	2022-09-20 08:39:06.357058+00	1	t	\N	f	f
620	CATEGORY	Category	CM556CRMO4 / Turbo charged	184683	2022-09-20 08:39:06.357162+00	2022-09-20 08:39:06.357206+00	1	t	\N	f	f
621	CATEGORY	Category	3TBA1Y8XTJ / Turbo charged	184682	2022-09-20 08:39:06.357301+00	2022-09-20 08:39:06.357335+00	1	t	\N	f	f
622	CATEGORY	Category	WUZT4BLA9Z / Turbo charged	184681	2022-09-20 08:39:06.357398+00	2022-09-20 08:39:06.357451+00	1	t	\N	f	f
623	CATEGORY	Category	SD6IFM5X2M / Turbo charged	184588	2022-09-20 08:39:06.357512+00	2022-09-20 08:39:06.357541+00	1	t	\N	f	f
624	CATEGORY	Category	3IFD3F0WJD / Turbo charged	184587	2022-09-20 08:39:06.357602+00	2022-09-20 08:39:06.357632+00	1	t	\N	f	f
625	CATEGORY	Category	Engine samp122123 / Turbo charged	184580	2022-09-20 08:39:06.357692+00	2022-09-20 08:39:06.357721+00	1	t	\N	f	f
626	CATEGORY	Category	Engine samp122 / Turbo charged	184264	2022-09-20 08:39:06.358058+00	2022-09-20 08:39:06.358315+00	1	t	\N	f	f
627	CATEGORY	Category	Engine samp1122 / Turbo charged	184130	2022-09-20 08:39:06.358592+00	2022-09-20 08:39:06.358641+00	1	t	\N	f	f
628	CATEGORY	Category	Engine samp112 / Turbo charged	184124	2022-09-20 08:39:06.359058+00	2022-09-20 08:39:06.359174+00	1	t	\N	f	f
629	CATEGORY	Category	Engine samp111 / Turbo charged	183963	2022-09-20 08:39:06.359435+00	2022-09-20 08:39:06.359465+00	1	t	\N	f	f
630	CATEGORY	Category	Engine samp11 / Turbo charged	183961	2022-09-20 08:39:06.359524+00	2022-09-20 08:39:06.359552+00	1	t	\N	f	f
631	CATEGORY	Category	Engine samp1 / Turbo charged	183959	2022-09-20 08:39:06.359609+00	2022-09-20 08:39:06.359636+00	1	t	\N	f	f
632	CATEGORY	Category	Engine samp / Turbo charged	183957	2022-09-20 08:39:06.359693+00	2022-09-20 08:39:06.35972+00	1	t	\N	f	f
633	CATEGORY	Category	Engine / Turbo charged	183955	2022-09-20 08:39:06.359777+00	2022-09-20 08:39:06.359804+00	1	t	\N	f	f
22	CATEGORY	Category	Internet	135456	2022-09-20 08:39:03.251324+00	2022-09-20 08:39:03.251363+00	1	t	\N	t	f
23	CATEGORY	Category	Meals	135741	2022-09-20 08:39:03.251536+00	2022-09-20 08:39:03.252214+00	1	t	\N	t	f
24	CATEGORY	Category	Airfare	135796	2022-09-20 08:39:03.252319+00	2022-09-20 08:39:03.252351+00	1	t	\N	t	f
25	CATEGORY	Category	Cell Phone	137946	2022-09-20 08:39:03.252415+00	2022-09-20 08:39:03.252443+00	1	t	\N	t	f
26	CATEGORY	Category	Ground Transportation-Parking	149332	2022-09-20 08:39:03.252505+00	2022-09-20 08:39:03.252534+00	1	t	\N	t	f
27	CATEGORY	Category	Hotel-Lodging	149333	2022-09-20 08:39:03.252594+00	2022-09-20 08:39:03.252623+00	1	t	\N	t	f
325	CATEGORY	Category	Food	135453	2022-09-20 08:39:05.265411+00	2022-09-20 08:49:07.925686+00	1	t	\N	f	f
3225	CATEGORY	Category	FML12E68S6 / Turbo charged	209304	2022-09-28 11:55:41.765972+00	2022-09-28 11:55:41.766025+00	1	t	\N	f	f
3226	CATEGORY	Category	N27HHEOEY8 / Turbo charged	209303	2022-09-28 11:55:41.766086+00	2022-09-28 11:55:41.766117+00	1	t	\N	f	f
3227	CATEGORY	Category	H7FH7Q9WJ6 / Turbo charged	209299	2022-09-28 11:55:41.76618+00	2022-09-28 11:55:41.766211+00	1	t	\N	f	f
921	PROJECT	Project	Celia Corp	247033	2022-09-20 08:39:07.403966+00	2022-09-20 08:39:07.403997+00	1	t	\N	f	f
635	PROJECT	Project	Bank West	300057	2022-09-20 08:39:06.833093+00	2022-09-20 08:39:06.833123+00	1	t	\N	f	f
636	PROJECT	Project	Basket Case	300058	2022-09-20 08:39:06.833177+00	2022-09-20 08:39:06.833207+00	1	t	\N	f	f
637	PROJECT	Project	Bayside Club	300059	2022-09-20 08:39:06.833716+00	2022-09-20 08:39:06.833753+00	1	t	\N	f	f
638	PROJECT	Project	Boom FM	300060	2022-09-20 08:39:06.833818+00	2022-09-20 08:39:06.83385+00	1	t	\N	f	f
639	PROJECT	Project	City Agency	300061	2022-09-20 08:39:06.833914+00	2022-09-20 08:39:06.83412+00	1	t	\N	f	f
640	PROJECT	Project	City Limousines	300062	2022-09-20 08:39:06.834233+00	2022-09-20 08:39:06.834501+00	1	t	\N	f	f
641	PROJECT	Project	DIISR - Small Business Services	300063	2022-09-20 08:39:06.834734+00	2022-09-20 08:39:06.834915+00	1	t	\N	f	f
642	PROJECT	Project	Hamilton Smith Ltd	300064	2022-09-20 08:39:06.835448+00	2022-09-20 08:39:06.835673+00	1	t	\N	f	f
643	PROJECT	Project	Marine Systems	300065	2022-09-20 08:39:06.835763+00	2022-09-20 08:39:06.835884+00	1	t	\N	f	f
644	PROJECT	Project	Petrie McLoud Watson & Associates	300066	2022-09-20 08:39:06.835949+00	2022-09-20 08:39:06.836424+00	1	t	\N	f	f
645	PROJECT	Project	Port & Philip Freight	300067	2022-09-20 08:39:06.83653+00	2022-09-20 08:39:06.836562+00	1	t	\N	f	f
646	PROJECT	Project	Rex Media Group	300068	2022-09-20 08:39:06.836641+00	2022-09-20 08:39:06.836682+00	1	t	\N	f	f
647	PROJECT	Project	Ridgeway University	300069	2022-09-20 08:39:06.836748+00	2022-09-20 08:39:06.836771+00	1	t	\N	f	f
648	PROJECT	Project	Young Bros Transport	300070	2022-09-20 08:39:06.836845+00	2022-09-20 08:39:06.836972+00	1	t	\N	f	f
649	PROJECT	Project	Chennai	299998	2022-09-20 08:39:06.837507+00	2022-09-20 08:39:06.837544+00	1	t	\N	f	f
650	PROJECT	Project	Delhi	299999	2022-09-20 08:39:06.837609+00	2022-09-20 08:39:06.83764+00	1	t	\N	f	f
651	PROJECT	Project	Sravan BLR Customer	299945	2022-09-20 08:39:06.837702+00	2022-09-20 08:39:06.837723+00	1	t	\N	f	f
652	PROJECT	Project	Bangalore	292304	2022-09-20 08:39:06.83778+00	2022-09-20 08:39:06.837801+00	1	t	\N	f	f
653	PROJECT	Project	Bebe Rexha	292305	2022-09-20 08:39:06.837862+00	2022-09-20 08:39:06.838575+00	1	t	\N	f	f
654	PROJECT	Project	suhas_p1	292306	2022-09-20 08:39:06.838741+00	2022-09-20 08:39:06.838765+00	1	t	\N	f	f
655	PROJECT	Project	Wow Company	292246	2022-09-20 08:39:06.839021+00	2022-09-20 08:39:06.839047+00	1	t	\N	f	f
656	PROJECT	Project	Nilesh Pant	292244	2022-09-20 08:39:06.83911+00	2022-09-20 08:39:06.83913+00	1	t	\N	f	f
657	PROJECT	Project	Project Sravan	292245	2022-09-20 08:39:06.839969+00	2022-09-20 08:39:06.840105+00	1	t	\N	f	f
658	PROJECT	Project	Adidas	292241	2022-09-20 08:39:06.843983+00	2022-09-20 08:39:06.844025+00	1	t	\N	f	f
659	PROJECT	Project	Fabrication	292242	2022-09-20 08:39:06.844369+00	2022-09-20 08:39:06.84444+00	1	t	\N	f	f
660	PROJECT	Project	FAE	292243	2022-09-20 08:39:06.844504+00	2022-09-20 08:39:06.844527+00	1	t	\N	f	f
661	PROJECT	Project	BOOK	292184	2022-09-20 08:39:06.844591+00	2022-09-20 08:39:06.844619+00	1	t	\N	f	f
662	PROJECT	Project	DevD	292185	2022-09-20 08:39:06.844673+00	2022-09-20 08:39:06.844696+00	1	t	\N	f	f
663	PROJECT	Project	DevH	292186	2022-09-20 08:39:06.84475+00	2022-09-20 08:39:06.845942+00	1	t	\N	f	f
664	PROJECT	Project	GB1-White	292187	2022-09-20 08:39:06.846084+00	2022-09-20 08:39:06.846117+00	1	t	\N	f	f
665	PROJECT	Project	GB3-White	292188	2022-09-20 08:39:06.846181+00	2022-09-20 08:39:06.84621+00	1	t	\N	f	f
666	PROJECT	Project	GB6-White	292189	2022-09-20 08:39:06.846271+00	2022-09-20 08:39:06.8463+00	1	t	\N	f	f
667	PROJECT	Project	GB9-White	292190	2022-09-20 08:39:06.846594+00	2022-09-20 08:39:06.846643+00	1	t	\N	f	f
668	PROJECT	Project	PMBr	292191	2022-09-20 08:39:06.846718+00	2022-09-20 08:39:06.846748+00	1	t	\N	f	f
669	PROJECT	Project	PMD	292192	2022-09-20 08:39:06.846809+00	2022-09-20 08:39:06.84683+00	1	t	\N	f	f
670	PROJECT	Project	PMDD	292193	2022-09-20 08:39:06.846884+00	2022-09-20 08:39:06.846905+00	1	t	\N	f	f
671	PROJECT	Project	PMWe	292194	2022-09-20 08:39:06.846958+00	2022-09-20 08:39:06.846983+00	1	t	\N	f	f
672	PROJECT	Project	Support-M	292195	2022-09-20 08:39:06.847026+00	2022-09-20 08:39:06.847037+00	1	t	\N	f	f
673	PROJECT	Project	TSL - Black	292196	2022-09-20 08:39:06.84709+00	2022-09-20 08:39:06.847135+00	1	t	\N	f	f
674	PROJECT	Project	TSM - Black	292197	2022-09-20 08:39:06.84732+00	2022-09-20 08:39:06.847397+00	1	t	\N	f	f
675	PROJECT	Project	TSS - Black	292198	2022-09-20 08:39:06.847555+00	2022-09-20 08:39:06.84758+00	1	t	\N	f	f
676	PROJECT	Project	Train-MS	292199	2022-09-20 08:39:06.847807+00	2022-09-20 08:39:06.848025+00	1	t	\N	f	f
677	PROJECT	Project	Project 1	203309	2022-09-20 08:39:06.848101+00	2022-09-20 08:39:06.848164+00	1	t	\N	f	f
678	PROJECT	Project	Project 2	203310	2022-09-20 08:39:06.848369+00	2022-09-20 08:39:06.848455+00	1	t	\N	f	f
685	PROJECT	Project	Project 9	203317	2022-09-20 08:39:06.867731+00	2022-09-20 08:39:06.867791+00	1	t	\N	f	f
686	PROJECT	Project	Project 10	203318	2022-09-20 08:39:06.868033+00	2022-09-20 08:39:06.868333+00	1	t	\N	f	f
687	PROJECT	Project	Fyle Team Integrations	243607	2022-09-20 08:39:06.868509+00	2022-09-20 08:39:06.868561+00	1	t	\N	f	f
689	PROJECT	Project	Customer Mapped Project	243609	2022-09-20 08:39:06.869203+00	2022-09-20 08:39:06.869358+00	1	t	\N	f	f
690	PROJECT	Project	Sage project fyle	243610	2022-09-20 08:39:06.869711+00	2022-09-20 08:39:06.869935+00	1	t	\N	f	f
691	PROJECT	Project	Sage Project 8	243611	2022-09-20 08:39:06.870078+00	2022-09-20 08:39:06.870123+00	1	t	\N	f	f
692	PROJECT	Project	Sage Project 5	243612	2022-09-20 08:39:06.870433+00	2022-09-20 08:39:06.87052+00	1	t	\N	f	f
693	PROJECT	Project	Sage Project 3	243613	2022-09-20 08:39:06.87061+00	2022-09-20 08:39:06.870633+00	1	t	\N	f	f
694	PROJECT	Project	Sage Project 1	243614	2022-09-20 08:39:06.870704+00	2022-09-20 08:39:06.870734+00	1	t	\N	f	f
695	PROJECT	Project	Sage Project 4	243615	2022-09-20 08:39:06.870804+00	2022-09-20 08:39:06.870836+00	1	t	\N	f	f
696	PROJECT	Project	Sravan Prod Test Pr@d	243616	2022-09-20 08:39:06.870929+00	2022-09-20 08:39:06.870955+00	1	t	\N	f	f
697	PROJECT	Project	Sage Project 9	243617	2022-09-20 08:39:06.871444+00	2022-09-20 08:39:06.871486+00	1	t	\N	f	f
698	PROJECT	Project	Sage Project 2	243618	2022-09-20 08:39:06.87156+00	2022-09-20 08:39:06.871574+00	1	t	\N	f	f
699	PROJECT	Project	Sage Project 6	243619	2022-09-20 08:39:06.871625+00	2022-09-20 08:39:06.871651+00	1	t	\N	f	f
700	PROJECT	Project	Sage Project 7	243620	2022-09-20 08:39:06.871705+00	2022-09-20 08:39:06.871739+00	1	t	\N	f	f
701	PROJECT	Project	Sage Project 10	243621	2022-09-20 08:39:06.872651+00	2022-09-20 08:39:06.872705+00	1	t	\N	f	f
702	PROJECT	Project	Fyle Main Project	243622	2022-09-20 08:39:06.874636+00	2022-09-20 08:39:06.874751+00	1	t	\N	f	f
703	PROJECT	Project	Amy's Bird Sanctuary	246788	2022-09-20 08:39:06.875893+00	2022-09-20 08:39:06.875974+00	1	t	\N	f	f
704	PROJECT	Project	Amy's Bird Sanctuary:Test Project	246789	2022-09-20 08:39:06.876307+00	2022-09-20 08:39:06.87636+00	1	t	\N	f	f
705	PROJECT	Project	Bill's Windsurf Shop	246790	2022-09-20 08:39:06.876609+00	2022-09-20 08:39:06.876654+00	1	t	\N	f	f
706	PROJECT	Project	Cool Cars	246791	2022-09-20 08:39:06.876789+00	2022-09-20 08:39:06.876845+00	1	t	\N	f	f
707	PROJECT	Project	Diego Rodriguez	246792	2022-09-20 08:39:06.87703+00	2022-09-20 08:39:06.877075+00	1	t	\N	f	f
708	PROJECT	Project	Diego Rodriguez:Test Project	246793	2022-09-20 08:39:06.877205+00	2022-09-20 08:39:06.877249+00	1	t	\N	f	f
709	PROJECT	Project	Dukes Basketball Camp	246794	2022-09-20 08:39:06.878025+00	2022-09-20 08:39:06.878107+00	1	t	\N	f	f
710	PROJECT	Project	Dylan Sollfrank	246795	2022-09-20 08:39:06.878781+00	2022-09-20 08:39:06.878974+00	1	t	\N	f	f
711	PROJECT	Project	Freeman Sporting Goods	246796	2022-09-20 08:39:06.879084+00	2022-09-20 08:39:06.879121+00	1	t	\N	f	f
712	PROJECT	Project	Freeman Sporting Goods:0969 Ocean View Road	246797	2022-09-20 08:39:06.879351+00	2022-09-20 08:39:06.879383+00	1	t	\N	f	f
713	PROJECT	Project	Freeman Sporting Goods:55 Twin Lane	246798	2022-09-20 08:39:06.879474+00	2022-09-20 08:39:06.879536+00	1	t	\N	f	f
714	PROJECT	Project	Geeta Kalapatapu	246799	2022-09-20 08:39:06.879692+00	2022-09-20 08:39:06.879741+00	1	t	\N	f	f
715	PROJECT	Project	Gevelber Photography	246800	2022-09-20 08:39:06.881907+00	2022-09-20 08:39:06.881962+00	1	t	\N	f	f
716	PROJECT	Project	Jeff's Jalopies	246801	2022-09-20 08:39:06.882444+00	2022-09-20 08:39:06.882498+00	1	t	\N	f	f
717	PROJECT	Project	John Melton	246802	2022-09-20 08:39:06.882581+00	2022-09-20 08:39:06.882614+00	1	t	\N	f	f
718	PROJECT	Project	Kate Whelan	246803	2022-09-20 08:39:06.882683+00	2022-09-20 08:39:06.882713+00	1	t	\N	f	f
719	PROJECT	Project	Kookies by Kathy	246804	2022-09-20 08:39:06.882777+00	2022-09-20 08:39:06.882807+00	1	t	\N	f	f
720	PROJECT	Project	Mark Cho	246805	2022-09-20 08:39:06.882871+00	2022-09-20 08:39:06.8829+00	1	t	\N	f	f
721	PROJECT	Project	Paulsen Medical Supplies	246806	2022-09-20 08:39:06.882963+00	2022-09-20 08:39:06.882992+00	1	t	\N	f	f
722	PROJECT	Project	Pye's Cakes	246807	2022-09-20 08:39:06.883054+00	2022-09-20 08:39:06.883076+00	1	t	\N	f	f
723	PROJECT	Project	Rago Travel Agency	246808	2022-09-20 08:39:06.883129+00	2022-09-20 08:39:06.883158+00	1	t	\N	f	f
724	PROJECT	Project	Red Rock Diner	246809	2022-09-20 08:39:06.88324+00	2022-09-20 08:39:06.88326+00	1	t	\N	f	f
725	PROJECT	Project	Rondonuwu Fruit and Vegi	246810	2022-09-20 08:39:06.883313+00	2022-09-20 08:39:06.883342+00	1	t	\N	f	f
726	PROJECT	Project	Shara Barnett	246811	2022-09-20 08:39:06.883531+00	2022-09-20 08:39:06.883551+00	1	t	\N	f	f
727	PROJECT	Project	Shara Barnett:Barnett Design	246812	2022-09-20 08:39:06.883602+00	2022-09-20 08:39:06.883631+00	1	t	\N	f	f
728	PROJECT	Project	Sheldon Cooper	246813	2022-09-20 08:39:06.883692+00	2022-09-20 08:39:06.883721+00	1	t	\N	f	f
729	PROJECT	Project	Sheldon Cooper:Incremental Project	246814	2022-09-20 08:39:06.883782+00	2022-09-20 08:39:06.88381+00	1	t	\N	f	f
730	PROJECT	Project	Sonnenschein Family Store	246815	2022-09-20 08:39:06.883863+00	2022-09-20 08:39:06.883883+00	1	t	\N	f	f
731	PROJECT	Project	Sushi by Katsuyuki	246816	2022-09-20 08:39:06.883945+00	2022-09-20 08:39:06.88397+00	1	t	\N	f	f
732	PROJECT	Project	Travis Waldron	246817	2022-09-20 08:39:06.884014+00	2022-09-20 08:39:06.884035+00	1	t	\N	f	f
733	PROJECT	Project	Video Games by Dan	246818	2022-09-20 08:39:06.884101+00	2022-09-20 08:39:06.884124+00	1	t	\N	f	f
734	PROJECT	Project	Wedding Planning by Whitney	246819	2022-09-20 08:39:06.893616+00	2022-09-20 08:39:06.893658+00	1	t	\N	f	f
735	PROJECT	Project	Weiskopf Consulting	246820	2022-09-20 08:39:06.893723+00	2022-09-20 08:39:06.893752+00	1	t	\N	f	f
736	PROJECT	Project	Ashwinnnnnn	246821	2022-09-20 08:39:06.893813+00	2022-09-20 08:39:06.893842+00	1	t	\N	f	f
737	PROJECT	Project	3M	246849	2022-09-20 08:39:06.893902+00	2022-09-20 08:39:06.89393+00	1	t	\N	f	f
738	PROJECT	Project	AB&I Holdings	246850	2022-09-20 08:39:06.89399+00	2022-09-20 08:39:06.894019+00	1	t	\N	f	f
739	PROJECT	Project	ACM Group	246851	2022-09-20 08:39:06.89408+00	2022-09-20 08:39:06.894108+00	1	t	\N	f	f
740	PROJECT	Project	AIM Accounting	246852	2022-09-20 08:39:06.894169+00	2022-09-20 08:39:06.894198+00	1	t	\N	f	f
741	PROJECT	Project	AIQ Networks	246853	2022-09-20 08:39:06.894259+00	2022-09-20 08:39:06.894288+00	1	t	\N	f	f
742	PROJECT	Project	AMG Inc	246854	2022-09-20 08:39:06.894686+00	2022-09-20 08:39:06.894735+00	1	t	\N	f	f
743	PROJECT	Project	Aaron Abbott	246855	2022-09-20 08:39:06.894808+00	2022-09-20 08:39:06.894839+00	1	t	\N	f	f
744	PROJECT	Project	Absolute Location Support	246856	2022-09-20 08:39:06.8949+00	2022-09-20 08:39:06.894929+00	1	t	\N	f	f
745	PROJECT	Project	Academy Avenue Liquor Store	246857	2022-09-20 08:39:06.894989+00	2022-09-20 08:39:06.895018+00	1	t	\N	f	f
746	PROJECT	Project	Academy Sports & Outdoors	246858	2022-09-20 08:39:06.895077+00	2022-09-20 08:39:06.895106+00	1	t	\N	f	f
747	PROJECT	Project	Academy Vision Science Clinic	246859	2022-09-20 08:39:06.895166+00	2022-09-20 08:39:06.895195+00	1	t	\N	f	f
748	PROJECT	Project	Accountants Inc	246860	2022-09-20 08:39:06.895255+00	2022-09-20 08:39:06.895284+00	1	t	\N	f	f
749	PROJECT	Project	Acera	246861	2022-09-20 08:39:06.895959+00	2022-09-20 08:39:06.896247+00	1	t	\N	f	f
750	PROJECT	Project	Acme Systems Incorporated	246862	2022-09-20 08:39:06.896514+00	2022-09-20 08:39:06.896546+00	1	t	\N	f	f
751	PROJECT	Project	AcuVision Eye Centre	246863	2022-09-20 08:39:06.89661+00	2022-09-20 08:39:06.89664+00	1	t	\N	f	f
752	PROJECT	Project	Advanced Design & Drafting Ltd	246864	2022-09-20 08:39:06.896701+00	2022-09-20 08:39:06.89673+00	1	t	\N	f	f
753	PROJECT	Project	Advanced Machining Techniques Inc.	246865	2022-09-20 08:39:06.896791+00	2022-09-20 08:39:06.89682+00	1	t	\N	f	f
754	PROJECT	Project	Agrela Apartments Agency	246866	2022-09-20 08:39:06.89688+00	2022-09-20 08:39:06.896909+00	1	t	\N	f	f
755	PROJECT	Project	Ahonen Catering Group	246867	2022-09-20 08:39:06.896969+00	2022-09-20 08:39:06.896998+00	1	t	\N	f	f
756	PROJECT	Project	Alain Henderson	246868	2022-09-20 08:39:06.897059+00	2022-09-20 08:39:06.897087+00	1	t	\N	f	f
757	PROJECT	Project	Alamo Catering Group	246869	2022-09-20 08:39:06.897148+00	2022-09-20 08:39:06.897176+00	1	t	\N	f	f
758	PROJECT	Project	Alchemy PR	246870	2022-09-20 08:39:06.897236+00	2022-09-20 08:39:06.897265+00	1	t	\N	f	f
759	PROJECT	Project	Alesna Leasing Sales	246871	2022-09-20 08:39:06.897325+00	2022-09-20 08:39:06.897354+00	1	t	\N	f	f
760	PROJECT	Project	Alex Benedet	246872	2022-09-20 08:39:06.897532+00	2022-09-20 08:39:06.897569+00	1	t	\N	f	f
761	PROJECT	Project	Alex Fabre	246873	2022-09-20 08:39:06.897633+00	2022-09-20 08:39:06.897662+00	1	t	\N	f	f
762	PROJECT	Project	Alex Wolfe	246874	2022-09-20 08:39:06.897722+00	2022-09-20 08:39:06.897751+00	1	t	\N	f	f
763	PROJECT	Project	All Occassions Event Coordination	246875	2022-09-20 08:39:06.897812+00	2022-09-20 08:39:06.897841+00	1	t	\N	f	f
764	PROJECT	Project	All Outdoors	246876	2022-09-20 08:39:06.897901+00	2022-09-20 08:39:06.89793+00	1	t	\N	f	f
765	PROJECT	Project	All World Produce	246877	2022-09-20 08:39:06.89799+00	2022-09-20 08:39:06.898018+00	1	t	\N	f	f
766	PROJECT	Project	All-Lift Inc	246878	2022-09-20 08:39:06.898078+00	2022-09-20 08:39:06.898107+00	1	t	\N	f	f
767	PROJECT	Project	Alpart	246879	2022-09-20 08:39:06.898167+00	2022-09-20 08:39:06.898196+00	1	t	\N	f	f
768	PROJECT	Project	Alpine Cafe and Wine Bar	246880	2022-09-20 08:39:06.898255+00	2022-09-20 08:39:06.898284+00	1	t	\N	f	f
769	PROJECT	Project	Altamirano Apartments Services	246881	2022-09-20 08:39:06.898442+00	2022-09-20 08:39:06.898479+00	1	t	\N	f	f
770	PROJECT	Project	Altonen Windows Rentals	246882	2022-09-20 08:39:06.898542+00	2022-09-20 08:39:06.898572+00	1	t	\N	f	f
771	PROJECT	Project	Amarillo Apartments Distributors	246883	2022-09-20 08:39:06.898632+00	2022-09-20 08:39:06.898661+00	1	t	\N	f	f
772	PROJECT	Project	Ambc	246884	2022-09-20 08:39:06.898722+00	2022-09-20 08:39:06.89875+00	1	t	\N	f	f
773	PROJECT	Project	AmerCaire	246885	2022-09-20 08:39:06.89881+00	2022-09-20 08:39:06.898839+00	1	t	\N	f	f
774	PROJECT	Project	Ammann Builders Fabricators	246886	2022-09-20 08:39:06.898899+00	2022-09-20 08:39:06.898927+00	1	t	\N	f	f
775	PROJECT	Project	Amsterdam Drug Store	246887	2022-09-20 08:39:06.898982+00	2022-09-20 08:39:06.899003+00	1	t	\N	f	f
776	PROJECT	Project	Amy Kall	246888	2022-09-20 08:39:06.899062+00	2022-09-20 08:39:06.899091+00	1	t	\N	f	f
777	PROJECT	Project	Anderson Boughton Inc.	246889	2022-09-20 08:39:06.899151+00	2022-09-20 08:39:06.89918+00	1	t	\N	f	f
778	PROJECT	Project	Andersson Hospital Inc.	246890	2022-09-20 08:39:06.899239+00	2022-09-20 08:39:06.899268+00	1	t	\N	f	f
779	PROJECT	Project	Andrew Mager	246891	2022-09-20 08:39:06.899329+00	2022-09-20 08:39:06.899358+00	1	t	\N	f	f
780	PROJECT	Project	Andy Johnson	246892	2022-09-20 08:39:06.899535+00	2022-09-20 08:39:06.899565+00	1	t	\N	f	f
781	PROJECT	Project	Andy Thompson	246893	2022-09-20 08:39:06.899626+00	2022-09-20 08:39:06.899655+00	1	t	\N	f	f
782	PROJECT	Project	Angerman Markets Company	246894	2022-09-20 08:39:06.899715+00	2022-09-20 08:39:06.899744+00	1	t	\N	f	f
783	PROJECT	Project	Anonymous Customer HQ	246895	2022-09-20 08:39:06.899805+00	2022-09-20 08:39:06.899834+00	1	t	\N	f	f
784	PROJECT	Project	Another Killer Product	246896	2022-09-20 08:39:06.911007+00	2022-09-20 08:39:06.911048+00	1	t	\N	f	f
785	PROJECT	Project	Another Killer Product 1	246897	2022-09-20 08:39:06.911108+00	2022-09-20 08:39:06.911129+00	1	t	\N	f	f
786	PROJECT	Project	Anthony Jacobs	246898	2022-09-20 08:39:06.911169+00	2022-09-20 08:39:06.91119+00	1	t	\N	f	f
787	PROJECT	Project	Antioch Construction Company	246899	2022-09-20 08:39:06.911368+00	2022-09-20 08:39:06.911397+00	1	t	\N	f	f
788	PROJECT	Project	Apfel Electric Co.	246900	2022-09-20 08:39:06.911453+00	2022-09-20 08:39:06.911474+00	1	t	\N	f	f
789	PROJECT	Project	Applications to go Inc	246901	2022-09-20 08:39:06.911535+00	2022-09-20 08:39:06.911554+00	1	t	\N	f	f
790	PROJECT	Project	Aquino Apartments Dynamics	246902	2022-09-20 08:39:06.911648+00	2022-09-20 08:39:06.911668+00	1	t	\N	f	f
791	PROJECT	Project	Arcizo Automotive Sales	246903	2022-09-20 08:39:06.911719+00	2022-09-20 08:39:06.91173+00	1	t	\N	f	f
792	PROJECT	Project	Arlington Software Management	246904	2022-09-20 08:39:06.91177+00	2022-09-20 08:39:06.911791+00	1	t	\N	f	f
793	PROJECT	Project	Arnold Tanner	246905	2022-09-20 08:39:06.911852+00	2022-09-20 08:39:06.911872+00	1	t	\N	f	f
794	PROJECT	Project	Arredla and Hillseth Hardware -	246906	2022-09-20 08:39:06.911958+00	2022-09-20 08:39:06.911978+00	1	t	\N	f	f
795	PROJECT	Project	Art Institute of California	246907	2022-09-20 08:39:06.912018+00	2022-09-20 08:39:06.912039+00	1	t	\N	f	f
796	PROJECT	Project	Asch _ Agency	246908	2022-09-20 08:39:06.912099+00	2022-09-20 08:39:06.912119+00	1	t	\N	f	f
797	PROJECT	Project	Ashley Smoth	246909	2022-09-20 08:39:06.912169+00	2022-09-20 08:39:06.912179+00	1	t	\N	f	f
798	PROJECT	Project	Ashton Consulting Ltd	246910	2022-09-20 08:39:06.912402+00	2022-09-20 08:39:06.912439+00	1	t	\N	f	f
799	PROJECT	Project	Aslanian Publishing Agency	246911	2022-09-20 08:39:06.91252+00	2022-09-20 08:39:06.912542+00	1	t	\N	f	f
800	PROJECT	Project	Astry Software Holding Corp.	246912	2022-09-20 08:39:06.91261+00	2022-09-20 08:39:06.912632+00	1	t	\N	f	f
801	PROJECT	Project	Atherton Grocery	246913	2022-09-20 08:39:06.912703+00	2022-09-20 08:39:06.912726+00	1	t	\N	f	f
802	PROJECT	Project	August Li	246914	2022-09-20 08:39:06.912798+00	2022-09-20 08:39:06.912823+00	1	t	\N	f	f
803	PROJECT	Project	Ausbrooks Construction Incorporated	246915	2022-09-20 08:39:06.912881+00	2022-09-20 08:39:06.912892+00	1	t	\N	f	f
804	PROJECT	Project	Austin Builders Distributors	246916	2022-09-20 08:39:06.912936+00	2022-09-20 08:39:06.912947+00	1	t	\N	f	f
805	PROJECT	Project	Austin Publishing Inc.	246917	2022-09-20 08:39:06.912993+00	2022-09-20 08:39:06.913005+00	1	t	\N	f	f
806	PROJECT	Project	Avac Supplies Ltd.	246918	2022-09-20 08:39:06.913051+00	2022-09-20 08:39:06.913062+00	1	t	\N	f	f
807	PROJECT	Project	Avani Walters	246919	2022-09-20 08:39:06.913107+00	2022-09-20 08:39:06.913117+00	1	t	\N	f	f
808	PROJECT	Project	Axxess Group	246920	2022-09-20 08:39:06.913162+00	2022-09-20 08:39:06.913172+00	1	t	\N	f	f
809	PROJECT	Project	B-Sharp Music	246921	2022-09-20 08:39:06.913218+00	2022-09-20 08:39:06.913229+00	1	t	\N	f	f
810	PROJECT	Project	BFI Inc	246922	2022-09-20 08:39:06.913274+00	2022-09-20 08:39:06.913285+00	1	t	\N	f	f
811	PROJECT	Project	Baim Lumber -	246923	2022-09-20 08:39:06.913494+00	2022-09-20 08:39:06.913516+00	1	t	\N	f	f
812	PROJECT	Project	Bakkala Catering Distributors	246924	2022-09-20 08:39:06.91356+00	2022-09-20 08:39:06.913572+00	1	t	\N	f	f
813	PROJECT	Project	Bankey and Marris Hardware Corporation	246925	2022-09-20 08:39:06.913616+00	2022-09-20 08:39:06.913626+00	1	t	\N	f	f
814	PROJECT	Project	Barham Automotive Services	246926	2022-09-20 08:39:06.913671+00	2022-09-20 08:39:06.913682+00	1	t	\N	f	f
815	PROJECT	Project	Barich Metal Fabricators Inc.	246927	2022-09-20 08:39:06.913729+00	2022-09-20 08:39:06.91374+00	1	t	\N	f	f
816	PROJECT	Project	Barners and Rushlow Liquors Sales	246928	2022-09-20 08:39:06.913784+00	2022-09-20 08:39:06.913796+00	1	t	\N	f	f
817	PROJECT	Project	Barnhurst Title Inc.	246929	2022-09-20 08:39:06.91384+00	2022-09-20 08:39:06.91385+00	1	t	\N	f	f
818	PROJECT	Project	Baron Chess	246930	2022-09-20 08:39:06.913897+00	2022-09-20 08:39:06.91391+00	1	t	\N	f	f
819	PROJECT	Project	Bartkus Automotive Company	246931	2022-09-20 08:39:06.913958+00	2022-09-20 08:39:06.913969+00	1	t	\N	f	f
820	PROJECT	Project	Baumgarn Windows and Associates	246932	2022-09-20 08:39:06.91401+00	2022-09-20 08:39:06.914022+00	1	t	\N	f	f
821	PROJECT	Project	Bay Media Research	246933	2022-09-20 08:39:06.914068+00	2022-09-20 08:39:06.914081+00	1	t	\N	f	f
822	PROJECT	Project	BaySide Office Space	246934	2022-09-20 08:39:06.91413+00	2022-09-20 08:39:06.914153+00	1	t	\N	f	f
823	PROJECT	Project	Bayas Hardware Dynamics	246935	2022-09-20 08:39:06.914201+00	2022-09-20 08:39:06.914213+00	1	t	\N	f	f
824	PROJECT	Project	Baylore	246936	2022-09-20 08:39:06.914259+00	2022-09-20 08:39:06.91427+00	1	t	\N	f	f
825	PROJECT	Project	Beams Electric Agency	246937	2022-09-20 08:39:06.914315+00	2022-09-20 08:39:06.914327+00	1	t	\N	f	f
826	PROJECT	Project	Beatie Leasing Networking	246938	2022-09-20 08:39:06.914467+00	2022-09-20 08:39:06.914499+00	1	t	\N	f	f
827	PROJECT	Project	Beattie Batteries	246939	2022-09-20 08:39:06.914567+00	2022-09-20 08:39:06.91458+00	1	t	\N	f	f
828	PROJECT	Project	Beaubien Antiques Leasing	246940	2022-09-20 08:39:06.914628+00	2022-09-20 08:39:06.91465+00	1	t	\N	f	f
829	PROJECT	Project	Belgrade Telecom -	246941	2022-09-20 08:39:06.914713+00	2022-09-20 08:39:06.91475+00	1	t	\N	f	f
830	PROJECT	Project	Belisle Title Networking	246942	2022-09-20 08:39:06.914811+00	2022-09-20 08:39:06.914831+00	1	t	\N	f	f
831	PROJECT	Project	Below Liquors Corporation	246943	2022-09-20 08:39:06.914901+00	2022-09-20 08:39:06.914921+00	1	t	\N	f	f
832	PROJECT	Project	Bemo Publishing Corporation	246944	2022-09-20 08:39:06.914995+00	2022-09-20 08:39:06.915037+00	1	t	\N	f	f
833	PROJECT	Project	Ben Lomond Software Incorporated	246945	2022-09-20 08:39:06.915118+00	2022-09-20 08:39:06.915138+00	1	t	\N	f	f
834	PROJECT	Project	Ben Sandler	246946	2022-09-20 08:39:07.372807+00	2022-09-20 08:39:07.372859+00	1	t	\N	f	f
835	PROJECT	Project	Benabides and Louris Builders Services	246947	2022-09-20 08:39:07.372936+00	2022-09-20 08:39:07.372967+00	1	t	\N	f	f
836	PROJECT	Project	Benbow Software	246948	2022-09-20 08:39:07.373036+00	2022-09-20 08:39:07.373303+00	1	t	\N	f	f
837	PROJECT	Project	Benge Liquors Incorporated	246949	2022-09-20 08:39:07.373382+00	2022-09-20 08:39:07.373412+00	1	t	\N	f	f
838	PROJECT	Project	Bennett Consulting	246950	2022-09-20 08:39:07.373481+00	2022-09-20 08:39:07.373511+00	1	t	\N	f	f
839	PROJECT	Project	Benton Construction Inc.	246951	2022-09-20 08:39:07.373719+00	2022-09-20 08:39:07.373779+00	1	t	\N	f	f
840	PROJECT	Project	Berliner Apartments Networking	246952	2022-09-20 08:39:07.373898+00	2022-09-20 08:39:07.373943+00	1	t	\N	f	f
841	PROJECT	Project	Berschauer Leasing Rentals	246953	2022-09-20 08:39:07.374057+00	2022-09-20 08:39:07.37409+00	1	t	\N	f	f
842	PROJECT	Project	Berthelette Antiques	246954	2022-09-20 08:39:07.374161+00	2022-09-20 08:39:07.374191+00	1	t	\N	f	f
843	PROJECT	Project	Bertot Attorneys Company	246955	2022-09-20 08:39:07.374257+00	2022-09-20 08:39:07.374287+00	1	t	\N	f	f
844	PROJECT	Project	Bertulli & Assoc	246956	2022-09-20 08:39:07.374695+00	2022-09-20 08:39:07.374729+00	1	t	\N	f	f
845	PROJECT	Project	Bethurum Telecom Sales	246957	2022-09-20 08:39:07.374796+00	2022-09-20 08:39:07.374833+00	1	t	\N	f	f
846	PROJECT	Project	Better Buy	246958	2022-09-20 08:39:07.37493+00	2022-09-20 08:39:07.37496+00	1	t	\N	f	f
847	PROJECT	Project	Bezak Construction Dynamics	246959	2022-09-20 08:39:07.375026+00	2022-09-20 08:39:07.375055+00	1	t	\N	f	f
848	PROJECT	Project	Bicycle Trailers	246960	2022-09-20 08:39:07.37512+00	2022-09-20 08:39:07.375149+00	1	t	\N	f	f
849	PROJECT	Project	Big 5 Sporting Goods	246961	2022-09-20 08:39:07.375228+00	2022-09-20 08:39:07.3754+00	1	t	\N	f	f
850	PROJECT	Project	Big Bear Lake Electric	246962	2022-09-20 08:39:07.375504+00	2022-09-20 08:39:07.375548+00	1	t	\N	f	f
851	PROJECT	Project	Big Bear Lake Plumbing Holding Corp.	246963	2022-09-20 08:39:07.375647+00	2022-09-20 08:39:07.375691+00	1	t	\N	f	f
852	PROJECT	Project	Billafuerte Software Company	246964	2022-09-20 08:39:07.375791+00	2022-09-20 08:39:07.375833+00	1	t	\N	f	f
853	PROJECT	Project	Bisonette Leasing	246965	2022-09-20 08:39:07.375969+00	2022-09-20 08:39:07.376015+00	1	t	\N	f	f
854	PROJECT	Project	Bleser Antiques Incorporated	246966	2022-09-20 08:39:07.376136+00	2022-09-20 08:39:07.376189+00	1	t	\N	f	f
855	PROJECT	Project	Blier Lumber Dynamics	246967	2022-09-20 08:39:07.376384+00	2022-09-20 08:39:07.376413+00	1	t	\N	f	f
856	PROJECT	Project	Blue Street Liquor Store	246968	2022-09-20 08:39:07.376506+00	2022-09-20 08:39:07.376551+00	1	t	\N	f	f
857	PROJECT	Project	Bob Ledner	246969	2022-09-20 08:39:07.376682+00	2022-09-20 08:39:07.376733+00	1	t	\N	f	f
858	PROJECT	Project	Bob Smith (bsmith@bobsmith.com)	246970	2022-09-20 08:39:07.376839+00	2022-09-20 08:39:07.376874+00	1	t	\N	f	f
859	PROJECT	Project	Bob Walsh Funiture Store	246971	2022-09-20 08:39:07.376951+00	2022-09-20 08:39:07.376978+00	1	t	\N	f	f
860	PROJECT	Project	Bobby Kelly	246972	2022-09-20 08:39:07.37704+00	2022-09-20 08:39:07.377067+00	1	t	\N	f	f
861	PROJECT	Project	Bobby Strands (Bobby@Strands.com)	246973	2022-09-20 08:39:07.377171+00	2022-09-20 08:39:07.37734+00	1	t	\N	f	f
862	PROJECT	Project	Bochenek and Skoog Liquors Company	246974	2022-09-20 08:39:07.377477+00	2022-09-20 08:39:07.377524+00	1	t	\N	f	f
863	PROJECT	Project	Bodfish Liquors Corporation	246975	2022-09-20 08:39:07.377629+00	2022-09-20 08:39:07.377659+00	1	t	\N	f	f
864	PROJECT	Project	Boise Antiques and Associates	246976	2022-09-20 08:39:07.37772+00	2022-09-20 08:39:07.377749+00	1	t	\N	f	f
865	PROJECT	Project	Boise Publishing Co.	246977	2022-09-20 08:39:07.377809+00	2022-09-20 08:39:07.377838+00	1	t	\N	f	f
866	PROJECT	Project	Boisselle Windows Distributors	246978	2022-09-20 08:39:07.377897+00	2022-09-20 08:39:07.377926+00	1	t	\N	f	f
867	PROJECT	Project	Bolder Construction Inc.	246979	2022-09-20 08:39:07.377986+00	2022-09-20 08:39:07.378015+00	1	t	\N	f	f
868	PROJECT	Project	Bollman Attorneys Company	246980	2022-09-20 08:39:07.378154+00	2022-09-20 08:39:07.3782+00	1	t	\N	f	f
869	PROJECT	Project	Bona Source	246981	2022-09-20 08:39:07.378379+00	2022-09-20 08:39:07.378409+00	1	t	\N	f	f
1585	PROJECT	Project	Sharon Stone	247697	2022-09-20 08:39:08.999158+00	2022-09-20 08:39:08.999186+00	1	t	\N	f	f
870	PROJECT	Project	Boney Electric Dynamics	246982	2022-09-20 08:39:07.378471+00	2022-09-20 08:39:07.3785+00	1	t	\N	f	f
871	PROJECT	Project	Borowski Catering Management	246983	2022-09-20 08:39:07.378596+00	2022-09-20 08:39:07.378638+00	1	t	\N	f	f
872	PROJECT	Project	Botero Electric Co.	246984	2022-09-20 08:39:07.378737+00	2022-09-20 08:39:07.378774+00	1	t	\N	f	f
873	PROJECT	Project	Bowling Green Painting Incorporated	246985	2022-09-20 08:39:07.378864+00	2022-09-20 08:39:07.378899+00	1	t	\N	f	f
874	PROJECT	Project	Boynton Beach Title Networking	246986	2022-09-20 08:39:07.378988+00	2022-09-20 08:39:07.379025+00	1	t	\N	f	f
875	PROJECT	Project	Bracken Works Inc	246987	2022-09-20 08:39:07.379115+00	2022-09-20 08:39:07.379153+00	1	t	\N	f	f
876	PROJECT	Project	Braithwaite Tech	246988	2022-09-20 08:39:07.379243+00	2022-09-20 08:39:07.379281+00	1	t	\N	f	f
877	PROJECT	Project	Bramucci Construction	246989	2022-09-20 08:39:07.379488+00	2022-09-20 08:39:07.379528+00	1	t	\N	f	f
878	PROJECT	Project	Brandwein Builders Fabricators	246990	2022-09-20 08:39:07.379618+00	2022-09-20 08:39:07.379656+00	1	t	\N	f	f
879	PROJECT	Project	Brea Painting Company	246991	2022-09-20 08:39:07.379744+00	2022-09-20 08:39:07.379797+00	1	t	\N	f	f
880	PROJECT	Project	Brent Apartments Rentals	246992	2022-09-20 08:39:07.379873+00	2022-09-20 08:39:07.379902+00	1	t	\N	f	f
881	PROJECT	Project	Brewers Retail	246993	2022-09-20 08:39:07.379963+00	2022-09-20 08:39:07.379992+00	1	t	\N	f	f
882	PROJECT	Project	Brick Metal Fabricators Services	246994	2022-09-20 08:39:07.380053+00	2022-09-20 08:39:07.380539+00	1	t	\N	f	f
883	PROJECT	Project	Bridgham Electric Inc.	246995	2022-09-20 08:39:07.380748+00	2022-09-20 08:39:07.380897+00	1	t	\N	f	f
884	PROJECT	Project	Bright Brothers Design	246996	2022-09-20 08:39:07.398587+00	2022-09-20 08:39:07.398627+00	1	t	\N	f	f
885	PROJECT	Project	Broadnay and Posthuma Lumber and Associates	246997	2022-09-20 08:39:07.398688+00	2022-09-20 08:39:07.398716+00	1	t	\N	f	f
886	PROJECT	Project	Brochard Metal Fabricators Incorporated	246998	2022-09-20 08:39:07.398772+00	2022-09-20 08:39:07.398799+00	1	t	\N	f	f
887	PROJECT	Project	Brosey Antiques -	246999	2022-09-20 08:39:07.398856+00	2022-09-20 08:39:07.398883+00	1	t	\N	f	f
888	PROJECT	Project	Bruce Storm	247000	2022-09-20 08:39:07.398939+00	2022-09-20 08:39:07.398966+00	1	t	\N	f	f
889	PROJECT	Project	Brutsch Builders Incorporated	247001	2022-09-20 08:39:07.399023+00	2022-09-20 08:39:07.39905+00	1	t	\N	f	f
890	PROJECT	Project	Brytor Inetrnational	247002	2022-09-20 08:39:07.399107+00	2022-09-20 08:39:07.399134+00	1	t	\N	f	f
891	PROJECT	Project	Burney and Oesterreich Title Manufacturing	247003	2022-09-20 08:39:07.399189+00	2022-09-20 08:39:07.399217+00	1	t	\N	f	f
892	PROJECT	Project	Buroker Markets Incorporated	247004	2022-09-20 08:39:07.399273+00	2022-09-20 08:39:07.3993+00	1	t	\N	f	f
893	PROJECT	Project	Busacker Liquors Services	247005	2022-09-20 08:39:07.399366+00	2022-09-20 08:39:07.399504+00	1	t	\N	f	f
894	PROJECT	Project	Bushnell	247006	2022-09-20 08:39:07.39956+00	2022-09-20 08:39:07.399571+00	1	t	\N	f	f
895	PROJECT	Project	By The Beach Cafe	247007	2022-09-20 08:39:07.399617+00	2022-09-20 08:39:07.399638+00	1	t	\N	f	f
896	PROJECT	Project	CH2M Hill Ltd	247008	2022-09-20 08:39:07.399698+00	2022-09-20 08:39:07.399728+00	1	t	\N	f	f
897	PROJECT	Project	CICA	247009	2022-09-20 08:39:07.399778+00	2022-09-20 08:39:07.39979+00	1	t	\N	f	f
898	PROJECT	Project	CIS Environmental Services	247010	2022-09-20 08:39:07.399839+00	2022-09-20 08:39:07.399868+00	1	t	\N	f	f
899	PROJECT	Project	CPS ltd	247011	2022-09-20 08:39:07.399927+00	2022-09-20 08:39:07.399948+00	1	t	\N	f	f
900	PROJECT	Project	CPSA	247012	2022-09-20 08:39:07.400008+00	2022-09-20 08:39:07.400037+00	1	t	\N	f	f
901	PROJECT	Project	CVM Business Solutions	247013	2022-09-20 08:39:07.400088+00	2022-09-20 08:39:07.400101+00	1	t	\N	f	f
902	PROJECT	Project	Caleb Attorneys Distributors	247014	2022-09-20 08:39:07.40015+00	2022-09-20 08:39:07.400179+00	1	t	\N	f	f
903	PROJECT	Project	Calley Leasing and Associates	247015	2022-09-20 08:39:07.400323+00	2022-09-20 08:39:07.400731+00	1	t	\N	f	f
904	PROJECT	Project	Cambareri Painting Sales	247016	2022-09-20 08:39:07.400868+00	2022-09-20 08:39:07.400894+00	1	t	\N	f	f
905	PROJECT	Project	Canadian Customer	247017	2022-09-20 08:39:07.400947+00	2022-09-20 08:39:07.400976+00	1	t	\N	f	f
906	PROJECT	Project	Canuck Door Systems Co.	247018	2022-09-20 08:39:07.401036+00	2022-09-20 08:39:07.401065+00	1	t	\N	f	f
907	PROJECT	Project	Capano Labs	247019	2022-09-20 08:39:07.401125+00	2022-09-20 08:39:07.401154+00	1	t	\N	f	f
908	PROJECT	Project	Caquias and Jank Catering Distributors	247020	2022-09-20 08:39:07.401321+00	2022-09-20 08:39:07.40136+00	1	t	\N	f	f
909	PROJECT	Project	Careymon Dudley	247021	2022-09-20 08:39:07.401421+00	2022-09-20 08:39:07.40145+00	1	t	\N	f	f
910	PROJECT	Project	Carloni Builders Company	247022	2022-09-20 08:39:07.401511+00	2022-09-20 08:39:07.40154+00	1	t	\N	f	f
911	PROJECT	Project	Carlos Beato	247023	2022-09-20 08:39:07.401595+00	2022-09-20 08:39:07.401615+00	1	t	\N	f	f
912	PROJECT	Project	Carmel Valley Metal Fabricators Holding Corp.	247024	2022-09-20 08:39:07.401675+00	2022-09-20 08:39:07.401705+00	1	t	\N	f	f
913	PROJECT	Project	Carpentersville Publishing	247025	2022-09-20 08:39:07.402175+00	2022-09-20 08:39:07.402212+00	1	t	\N	f	f
914	PROJECT	Project	Carpinteria Leasing Services	247026	2022-09-20 08:39:07.402493+00	2022-09-20 08:39:07.402524+00	1	t	\N	f	f
915	PROJECT	Project	Carrie Davis	247027	2022-09-20 08:39:07.403082+00	2022-09-20 08:39:07.403117+00	1	t	\N	f	f
916	PROJECT	Project	Cash & Warren	247028	2022-09-20 08:39:07.403169+00	2022-09-20 08:39:07.40319+00	1	t	\N	f	f
917	PROJECT	Project	Castek Inc	247029	2022-09-20 08:39:07.403339+00	2022-09-20 08:39:07.403369+00	1	t	\N	f	f
918	PROJECT	Project	Casuse Liquors Inc.	247030	2022-09-20 08:39:07.40343+00	2022-09-20 08:39:07.403458+00	1	t	\N	f	f
919	PROJECT	Project	Cathy Thoms	247031	2022-09-20 08:39:07.403533+00	2022-09-20 08:39:07.403653+00	1	t	\N	f	f
920	PROJECT	Project	Cawthron and Ullo Windows Corporation	247032	2022-09-20 08:39:07.403834+00	2022-09-20 08:39:07.403879+00	1	t	\N	f	f
922	PROJECT	Project	Central Islip Antiques Fabricators	247034	2022-09-20 08:39:07.404073+00	2022-09-20 08:39:07.404106+00	1	t	\N	f	f
923	PROJECT	Project	Cerritos Telecom and Associates	247035	2022-09-20 08:39:07.404202+00	2022-09-20 08:39:07.404237+00	1	t	\N	f	f
924	PROJECT	Project	Chamberlain Service Ltd	247036	2022-09-20 08:39:07.404472+00	2022-09-20 08:39:07.404495+00	1	t	\N	f	f
925	PROJECT	Project	Champaign Painting Rentals	247037	2022-09-20 08:39:07.404556+00	2022-09-20 08:39:07.404577+00	1	t	\N	f	f
926	PROJECT	Project	Chandrasekara Markets Sales	247038	2022-09-20 08:39:07.404621+00	2022-09-20 08:39:07.404641+00	1	t	\N	f	f
927	PROJECT	Project	Channer Antiques Dynamics	247039	2022-09-20 08:39:07.404696+00	2022-09-20 08:39:07.404717+00	1	t	\N	f	f
928	PROJECT	Project	Charlotte Hospital Incorporated	247040	2022-09-20 08:39:07.404777+00	2022-09-20 08:39:07.404806+00	1	t	\N	f	f
929	PROJECT	Project	Cheese Factory	247041	2022-09-20 08:39:07.404866+00	2022-09-20 08:39:07.404895+00	1	t	\N	f	f
930	PROJECT	Project	Chess Art Gallery	247042	2022-09-20 08:39:07.404976+00	2022-09-20 08:39:07.405127+00	1	t	\N	f	f
931	PROJECT	Project	Chiaminto Attorneys Agency	247043	2022-09-20 08:39:07.405446+00	2022-09-20 08:39:07.405496+00	1	t	\N	f	f
932	PROJECT	Project	China Cuisine	247044	2022-09-20 08:39:07.405601+00	2022-09-20 08:39:07.405649+00	1	t	\N	f	f
933	PROJECT	Project	Chittenden _ Agency	247045	2022-09-20 08:39:07.405738+00	2022-09-20 08:39:07.405758+00	1	t	\N	f	f
934	PROJECT	Project	Cino & Cino	247046	2022-09-20 08:39:07.422009+00	2022-09-20 08:39:07.422077+00	1	t	\N	f	f
935	PROJECT	Project	Circuit Cities	247047	2022-09-20 08:39:07.4225+00	2022-09-20 08:39:07.423089+00	1	t	\N	f	f
936	PROJECT	Project	Clayton and Bubash Telecom Services	247048	2022-09-20 08:39:07.426042+00	2022-09-20 08:39:07.426075+00	1	t	\N	f	f
937	PROJECT	Project	Clubb Electric Co.	247049	2022-09-20 08:39:07.427139+00	2022-09-20 08:39:07.42751+00	1	t	\N	f	f
938	PROJECT	Project	Cochell Markets Group	247050	2022-09-20 08:39:07.427671+00	2022-09-20 08:39:07.428511+00	1	t	\N	f	f
939	PROJECT	Project	Coen Publishing Co.	247051	2022-09-20 08:39:07.428747+00	2022-09-20 08:39:07.428931+00	1	t	\N	f	f
940	PROJECT	Project	Coklow Leasing Dynamics	247052	2022-09-20 08:39:07.429722+00	2022-09-20 08:39:07.429775+00	1	t	\N	f	f
941	PROJECT	Project	Coletta Hospital Inc.	247053	2022-09-20 08:39:07.430023+00	2022-09-20 08:39:07.430073+00	1	t	\N	f	f
942	PROJECT	Project	Colony Antiques	247054	2022-09-20 08:39:07.430394+00	2022-09-20 08:39:07.430424+00	1	t	\N	f	f
943	PROJECT	Project	Colorado Springs Leasing Fabricators	247055	2022-09-20 08:39:07.430483+00	2022-09-20 08:39:07.43052+00	1	t	\N	f	f
944	PROJECT	Project	Colosimo Catering and Associates	247056	2022-09-20 08:39:07.43059+00	2022-09-20 08:39:07.430628+00	1	t	\N	f	f
945	PROJECT	Project	Computer Literacy	247057	2022-09-20 08:39:07.431167+00	2022-09-20 08:39:07.431323+00	1	t	\N	f	f
946	PROJECT	Project	Computer Training Associates	247058	2022-09-20 08:39:07.431391+00	2022-09-20 08:39:07.431413+00	1	t	\N	f	f
947	PROJECT	Project	Connectus	247059	2022-09-20 08:39:07.431468+00	2022-09-20 08:39:07.4315+00	1	t	\N	f	f
948	PROJECT	Project	Constanza Liquors -	247060	2022-09-20 08:39:07.431896+00	2022-09-20 08:39:07.431927+00	1	t	\N	f	f
949	PROJECT	Project	Conteras Liquors Agency	247061	2022-09-20 08:39:07.43198+00	2022-09-20 08:39:07.432001+00	1	t	\N	f	f
950	PROJECT	Project	Conterras and Katen Attorneys Services	247062	2022-09-20 08:39:07.432058+00	2022-09-20 08:39:07.432079+00	1	t	\N	f	f
951	PROJECT	Project	Convery Attorneys and Associates	247063	2022-09-20 08:39:07.432413+00	2022-09-20 08:39:07.432438+00	1	t	\N	f	f
952	PROJECT	Project	Conway Products	247064	2022-09-20 08:39:07.432497+00	2022-09-20 08:39:07.432518+00	1	t	\N	f	f
953	PROJECT	Project	Cooler Title Company	247065	2022-09-20 08:39:07.432571+00	2022-09-20 08:39:07.432655+00	1	t	\N	f	f
954	PROJECT	Project	Cooper Equipment	247066	2022-09-20 08:39:07.432712+00	2022-09-20 08:39:07.432733+00	1	t	\N	f	f
955	PROJECT	Project	Cooper Industries	247067	2022-09-20 08:39:07.432794+00	2022-09-20 08:39:07.432823+00	1	t	\N	f	f
956	PROJECT	Project	Core Care Canada	247068	2022-09-20 08:39:07.432884+00	2022-09-20 08:39:07.433138+00	1	t	\N	f	f
957	PROJECT	Project	Core Care Technologies Inc.	247069	2022-09-20 08:39:07.433474+00	2022-09-20 08:39:07.433507+00	1	t	\N	f	f
958	PROJECT	Project	Coressel _ -	247070	2022-09-20 08:39:07.433706+00	2022-09-20 08:39:07.433792+00	1	t	\N	f	f
959	PROJECT	Project	Cosimini Software Agency	247071	2022-09-20 08:39:07.433881+00	2022-09-20 08:39:07.433992+00	1	t	\N	f	f
960	PROJECT	Project	Cotterman Software Company	247072	2022-09-20 08:39:07.43405+00	2022-09-20 08:39:07.434136+00	1	t	\N	f	f
961	PROJECT	Project	Cottew Publishing Inc.	247073	2022-09-20 08:39:07.434192+00	2022-09-20 08:39:07.434213+00	1	t	\N	f	f
962	PROJECT	Project	Cottman Publishing Manufacturing	247074	2022-09-20 08:39:07.434466+00	2022-09-20 08:39:07.434575+00	1	t	\N	f	f
963	PROJECT	Project	Coxum Software Dynamics	247075	2022-09-20 08:39:07.434741+00	2022-09-20 08:39:07.434767+00	1	t	\N	f	f
964	PROJECT	Project	Cray Systems	247076	2022-09-20 08:39:07.434816+00	2022-09-20 08:39:07.434837+00	1	t	\N	f	f
965	PROJECT	Project	Creasman Antiques Holding Corp.	247077	2022-09-20 08:39:07.435453+00	2022-09-20 08:39:07.435499+00	1	t	\N	f	f
966	PROJECT	Project	Creighton & Company	247078	2022-09-20 08:39:07.435579+00	2022-09-20 08:39:07.435608+00	1	t	\N	f	f
967	PROJECT	Project	Crighton Catering Company	247079	2022-09-20 08:39:07.435984+00	2022-09-20 08:39:07.43603+00	1	t	\N	f	f
968	PROJECT	Project	Crisafulli Hardware Holding Corp.	247080	2022-09-20 08:39:07.436318+00	2022-09-20 08:39:07.43635+00	1	t	\N	f	f
969	PROJECT	Project	Cruce Builders	247081	2022-09-20 08:39:07.436405+00	2022-09-20 08:39:07.436419+00	1	t	\N	f	f
970	PROJECT	Project	Culprit Inc.	247082	2022-09-20 08:39:07.436469+00	2022-09-20 08:39:07.436489+00	1	t	\N	f	f
971	PROJECT	Project	Cwik and Klayman Metal Fabricators Holding Corp.	247083	2022-09-20 08:39:07.436542+00	2022-09-20 08:39:07.436571+00	1	t	\N	f	f
972	PROJECT	Project	Cytec Industries Inc	247084	2022-09-20 08:39:07.436732+00	2022-09-20 08:39:07.436777+00	1	t	\N	f	f
973	PROJECT	Project	D&H Manufacturing	247085	2022-09-20 08:39:07.437477+00	2022-09-20 08:39:07.437554+00	1	t	\N	f	f
974	PROJECT	Project	Dale Jenson	247086	2022-09-20 08:39:07.437743+00	2022-09-20 08:39:07.437773+00	1	t	\N	f	f
975	PROJECT	Project	Dambrose and Ottum Leasing Holding Corp.	247087	2022-09-20 08:39:07.437921+00	2022-09-20 08:39:07.437947+00	1	t	\N	f	f
1190	PROJECT	Project	Iain Bennett	247302	2022-09-20 08:39:07.944534+00	2022-09-20 08:39:07.944573+00	1	t	\N	f	f
976	PROJECT	Project	Danniels Antiques Inc.	247088	2022-09-20 08:39:07.438046+00	2022-09-20 08:39:07.438088+00	1	t	\N	f	f
977	PROJECT	Project	Daquino Painting -	247089	2022-09-20 08:39:07.438424+00	2022-09-20 08:39:07.438438+00	1	t	\N	f	f
978	PROJECT	Project	Dary Construction Corporation	247090	2022-09-20 08:39:07.43884+00	2022-09-20 08:39:07.438879+00	1	t	\N	f	f
979	PROJECT	Project	David Langhor	247091	2022-09-20 08:39:07.438955+00	2022-09-20 08:39:07.438984+00	1	t	\N	f	f
980	PROJECT	Project	Days Creek Electric Services	247092	2022-09-20 08:39:07.439203+00	2022-09-20 08:39:07.439673+00	1	t	\N	f	f
981	PROJECT	Project	Deblasio Painting Holding Corp.	247093	2022-09-20 08:39:07.439801+00	2022-09-20 08:39:07.439847+00	1	t	\N	f	f
982	PROJECT	Project	Defaveri Construction	247094	2022-09-20 08:39:07.439977+00	2022-09-20 08:39:07.440015+00	1	t	\N	f	f
983	PROJECT	Project	Dehaney Liquors Co.	247095	2022-09-20 08:39:07.44008+00	2022-09-20 08:39:07.44011+00	1	t	\N	f	f
984	PROJECT	Project	DelRey Distributors	247096	2022-09-20 08:39:07.460764+00	2022-09-20 08:39:07.460811+00	1	t	\N	f	f
985	PROJECT	Project	DellPack (UK)	247097	2022-09-20 08:39:07.46088+00	2022-09-20 08:39:07.460909+00	1	t	\N	f	f
986	PROJECT	Project	Demaire Automotive Systems	247098	2022-09-20 08:39:07.460972+00	2022-09-20 08:39:07.460994+00	1	t	\N	f	f
987	PROJECT	Project	Denise Sweet	247099	2022-09-20 08:39:07.46104+00	2022-09-20 08:39:07.461052+00	1	t	\N	f	f
988	PROJECT	Project	Dennis Batemanger	247100	2022-09-20 08:39:07.461101+00	2022-09-20 08:39:07.46113+00	1	t	\N	f	f
989	PROJECT	Project	Diamond Bar Plumbing	247101	2022-09-20 08:39:07.461726+00	2022-09-20 08:39:07.46203+00	1	t	\N	f	f
990	PROJECT	Project	Diekema Attorneys Manufacturing	247102	2022-09-20 08:39:07.462631+00	2022-09-20 08:39:07.462663+00	1	t	\N	f	f
991	PROJECT	Project	Difebbo and Lewelling Markets Agency	247103	2022-09-20 08:39:07.462721+00	2022-09-20 08:39:07.462743+00	1	t	\N	f	f
992	PROJECT	Project	Dillain Collins	247104	2022-09-20 08:39:07.462809+00	2022-09-20 08:39:07.462838+00	1	t	\N	f	f
993	PROJECT	Project	Diluzio Automotive Group	247105	2022-09-20 08:39:07.462938+00	2022-09-20 08:39:07.463894+00	1	t	\N	f	f
994	PROJECT	Project	Dipiano Automotive Sales	247106	2022-09-20 08:39:07.464158+00	2022-09-20 08:39:07.464202+00	1	t	\N	f	f
995	PROJECT	Project	Doerrer Apartments Inc.	247107	2022-09-20 08:39:07.464945+00	2022-09-20 08:39:07.465024+00	1	t	\N	f	f
996	PROJECT	Project	Dogan Painting Leasing	247108	2022-09-20 08:39:07.465603+00	2022-09-20 08:39:07.465749+00	1	t	\N	f	f
997	PROJECT	Project	Doiel and Mcdivitt Construction Holding Corp.	247109	2022-09-20 08:39:07.465917+00	2022-09-20 08:39:07.465944+00	1	t	\N	f	f
998	PROJECT	Project	Dolfi Software Group	247110	2022-09-20 08:39:07.466148+00	2022-09-20 08:39:07.46618+00	1	t	\N	f	f
999	PROJECT	Project	Dominion Consulting	247111	2022-09-20 08:39:07.466238+00	2022-09-20 08:39:07.466253+00	1	t	\N	f	f
1000	PROJECT	Project	Dorey Attorneys Distributors	247112	2022-09-20 08:39:07.466294+00	2022-09-20 08:39:07.466315+00	1	t	\N	f	f
1001	PROJECT	Project	Dorminy Windows Rentals	247113	2022-09-20 08:39:07.467103+00	2022-09-20 08:39:07.467142+00	1	t	\N	f	f
1002	PROJECT	Project	Douse Telecom Leasing	247114	2022-09-20 08:39:07.467562+00	2022-09-20 08:39:07.467591+00	1	t	\N	f	f
1003	PROJECT	Project	Downey Catering Agency	247115	2022-09-20 08:39:07.46766+00	2022-09-20 08:39:07.467694+00	1	t	\N	f	f
1004	PROJECT	Project	Downey and Sweezer Electric Group	247116	2022-09-20 08:39:07.46811+00	2022-09-20 08:39:07.468144+00	1	t	\N	f	f
1005	PROJECT	Project	Dries Hospital Manufacturing	247117	2022-09-20 08:39:07.468216+00	2022-09-20 08:39:07.468258+00	1	t	\N	f	f
1006	PROJECT	Project	Drown Markets Services	247118	2022-09-20 08:39:07.468729+00	2022-09-20 08:39:07.468762+00	1	t	\N	f	f
1007	PROJECT	Project	Drumgoole Attorneys Corporation	247119	2022-09-20 08:39:07.468873+00	2022-09-20 08:39:07.468898+00	1	t	\N	f	f
1008	PROJECT	Project	Duhamel Lumber Co.	247120	2022-09-20 08:39:07.468951+00	2022-09-20 08:39:07.468976+00	1	t	\N	f	f
1009	PROJECT	Project	Duman Windows Sales	247121	2022-09-20 08:39:07.469029+00	2022-09-20 08:39:07.469097+00	1	t	\N	f	f
1010	PROJECT	Project	Dunlevy Software Corporation	247122	2022-09-20 08:39:07.46959+00	2022-09-20 08:39:07.469614+00	1	t	\N	f	f
1011	PROJECT	Project	Duroseau Publishing	247123	2022-09-20 08:39:07.469682+00	2022-09-20 08:39:07.46971+00	1	t	\N	f	f
1012	PROJECT	Project	Eachus Metal Fabricators Incorporated	247124	2022-09-20 08:39:07.469756+00	2022-09-20 08:39:07.469777+00	1	t	\N	f	f
1013	PROJECT	Project	Eberlein and Preslipsky _ Holding Corp.	247125	2022-09-20 08:39:07.477884+00	2022-09-20 08:39:07.47816+00	1	t	\N	f	f
1014	PROJECT	Project	Eckerman Leasing Management	247126	2022-09-20 08:39:07.478266+00	2022-09-20 08:39:07.478301+00	1	t	\N	f	f
1015	PROJECT	Project	Eckler Leasing	247127	2022-09-20 08:39:07.478828+00	2022-09-20 08:39:07.47894+00	1	t	\N	f	f
1016	PROJECT	Project	Eckrote Construction Fabricators	247128	2022-09-20 08:39:07.479018+00	2022-09-20 08:39:07.479039+00	1	t	\N	f	f
1017	PROJECT	Project	Ed Obuz	247129	2022-09-20 08:39:07.479169+00	2022-09-20 08:39:07.479201+00	1	t	\N	f	f
1018	PROJECT	Project	Ede Title Rentals	247130	2022-09-20 08:39:07.479539+00	2022-09-20 08:39:07.479574+00	1	t	\N	f	f
1019	PROJECT	Project	Edin Lumber Distributors	247131	2022-09-20 08:39:07.479627+00	2022-09-20 08:39:07.479649+00	1	t	\N	f	f
1020	PROJECT	Project	Effectiovation Inc	247132	2022-09-20 08:39:07.479703+00	2022-09-20 08:39:07.479724+00	1	t	\N	f	f
1021	PROJECT	Project	Efficiency Engineering	247133	2022-09-20 08:39:07.479801+00	2022-09-20 08:39:07.480171+00	1	t	\N	f	f
1022	PROJECT	Project	Eichner Antiques -	247134	2022-09-20 08:39:07.480343+00	2022-09-20 08:39:07.48037+00	1	t	\N	f	f
1023	PROJECT	Project	El Paso Hardware Co.	247135	2022-09-20 08:39:07.480434+00	2022-09-20 08:39:07.480464+00	1	t	\N	f	f
1024	PROJECT	Project	Electronics Direct to You	247136	2022-09-20 08:39:07.48076+00	2022-09-20 08:39:07.480791+00	1	t	\N	f	f
1025	PROJECT	Project	Elegance Interior Design	247137	2022-09-20 08:39:07.481279+00	2022-09-20 08:39:07.481319+00	1	t	\N	f	f
1026	PROJECT	Project	Eliszewski Windows Dynamics	247138	2022-09-20 08:39:07.481426+00	2022-09-20 08:39:07.481823+00	1	t	\N	f	f
1027	PROJECT	Project	Ellenberger Windows Management	247139	2022-09-20 08:39:07.481906+00	2022-09-20 08:39:07.481929+00	1	t	\N	f	f
1028	PROJECT	Project	Emergys	247140	2022-09-20 08:39:07.482039+00	2022-09-20 08:39:07.482062+00	1	t	\N	f	f
1029	PROJECT	Project	Empire Financial Group	247141	2022-09-20 08:39:07.482115+00	2022-09-20 08:39:07.482136+00	1	t	\N	f	f
1030	PROJECT	Project	Engelkemier Catering Management	247142	2022-09-20 08:39:07.482186+00	2022-09-20 08:39:07.4822+00	1	t	\N	f	f
1031	PROJECT	Project	Epling Builders Inc.	247143	2022-09-20 08:39:07.48289+00	2022-09-20 08:39:07.482928+00	1	t	\N	f	f
1032	PROJECT	Project	Eric Korb	247144	2022-09-20 08:39:07.483238+00	2022-09-20 08:39:07.483276+00	1	t	\N	f	f
1033	PROJECT	Project	Eric Schmidt	247145	2022-09-20 08:39:07.483343+00	2022-09-20 08:39:07.483674+00	1	t	\N	f	f
1034	PROJECT	Project	Erin Kessman	247146	2022-09-20 08:39:07.907998+00	2022-09-20 08:39:07.908042+00	1	t	\N	f	f
1035	PROJECT	Project	Ertle Painting Leasing	247147	2022-09-20 08:39:07.908108+00	2022-09-20 08:39:07.908137+00	1	t	\N	f	f
1036	PROJECT	Project	Espar Heater Systems	247148	2022-09-20 08:39:07.90836+00	2022-09-20 08:39:07.90839+00	1	t	\N	f	f
1037	PROJECT	Project	Estanislau and Brodka Electric Holding Corp.	247149	2022-09-20 08:39:07.908461+00	2022-09-20 08:39:07.908489+00	1	t	\N	f	f
1038	PROJECT	Project	Estee Lauder	247150	2022-09-20 08:39:07.908548+00	2022-09-20 08:39:07.908576+00	1	t	\N	f	f
1039	PROJECT	Project	Estevez Title and Associates	247151	2022-09-20 08:39:07.908634+00	2022-09-20 08:39:07.908661+00	1	t	\N	f	f
1040	PROJECT	Project	Eugenio	247152	2022-09-20 08:39:07.908719+00	2022-09-20 08:39:07.908746+00	1	t	\N	f	f
1041	PROJECT	Project	Evans Leasing Fabricators	247153	2022-09-20 08:39:07.908803+00	2022-09-20 08:39:07.90883+00	1	t	\N	f	f
1042	PROJECT	Project	Everett Fine Wines	247154	2022-09-20 08:39:07.908888+00	2022-09-20 08:39:07.908915+00	1	t	\N	f	f
1043	PROJECT	Project	Everett International	247155	2022-09-20 08:39:07.909026+00	2022-09-20 08:39:07.909057+00	1	t	\N	f	f
1044	PROJECT	Project	Eyram Marketing	247156	2022-09-20 08:39:07.909118+00	2022-09-20 08:39:07.909152+00	1	t	\N	f	f
1045	PROJECT	Project	FA-HB Inc.	247157	2022-09-20 08:39:07.909311+00	2022-09-20 08:39:07.909333+00	1	t	\N	f	f
1046	PROJECT	Project	FA-HB Job	247158	2022-09-20 08:39:07.909387+00	2022-09-20 08:39:07.909409+00	1	t	\N	f	f
1047	PROJECT	Project	FSI Industries (EUR)	247159	2022-09-20 08:39:07.909452+00	2022-09-20 08:39:07.909473+00	1	t	\N	f	f
1048	PROJECT	Project	Fabre Enterprises	247160	2022-09-20 08:39:07.909533+00	2022-09-20 08:39:07.909572+00	1	t	\N	f	f
1049	PROJECT	Project	Fabrizio's Dry Cleaners	247161	2022-09-20 08:39:07.909628+00	2022-09-20 08:39:07.909655+00	1	t	\N	f	f
1050	PROJECT	Project	Fagnani Builders	247162	2022-09-20 08:39:07.909712+00	2022-09-20 08:39:07.909739+00	1	t	\N	f	f
1051	PROJECT	Project	Falls Church _ Agency	247163	2022-09-20 08:39:07.909795+00	2022-09-20 08:39:07.909823+00	1	t	\N	f	f
1052	PROJECT	Project	Fantasy Gemmart	247164	2022-09-20 08:39:07.909879+00	2022-09-20 08:39:07.909906+00	1	t	\N	f	f
1053	PROJECT	Project	Fasefax Systems	247165	2022-09-20 08:39:07.909963+00	2022-09-20 08:39:07.90999+00	1	t	\N	f	f
1054	PROJECT	Project	Faske Software Group	247166	2022-09-20 08:39:07.910046+00	2022-09-20 08:39:07.910073+00	1	t	\N	f	f
1055	PROJECT	Project	Fauerbach _ Agency	247167	2022-09-20 08:39:07.910129+00	2022-09-20 08:39:07.910156+00	1	t	\N	f	f
1056	PROJECT	Project	Fenceroy and Herling Metal Fabricators Management	247168	2022-09-20 08:39:07.910213+00	2022-09-20 08:39:07.91024+00	1	t	\N	f	f
1057	PROJECT	Project	Fernstrom Automotive Systems	247169	2022-09-20 08:39:07.910296+00	2022-09-20 08:39:07.910323+00	1	t	\N	f	f
1058	PROJECT	Project	Ferrio and Donlon Builders Management	247170	2022-09-20 08:39:07.910379+00	2022-09-20 08:39:07.91042+00	1	t	\N	f	f
1059	PROJECT	Project	Fetterolf and Loud Apartments Inc.	247171	2022-09-20 08:39:07.91059+00	2022-09-20 08:39:07.910618+00	1	t	\N	f	f
1060	PROJECT	Project	Ficke Apartments Group	247172	2022-09-20 08:39:07.910674+00	2022-09-20 08:39:07.910701+00	1	t	\N	f	f
1061	PROJECT	Project	FigmentSoft Inc	247173	2022-09-20 08:39:07.910758+00	2022-09-20 08:39:07.910784+00	1	t	\N	f	f
1062	PROJECT	Project	Fiore Fashion Inc	247174	2022-09-20 08:39:07.910841+00	2022-09-20 08:39:07.910868+00	1	t	\N	f	f
1063	PROJECT	Project	Florence Liquors and Associates	247175	2022-09-20 08:39:07.910924+00	2022-09-20 08:39:07.910951+00	1	t	\N	f	f
1064	PROJECT	Project	Flores Inc	247176	2022-09-20 08:39:07.911006+00	2022-09-20 08:39:07.911033+00	1	t	\N	f	f
1065	PROJECT	Project	Focal Point Opticians	247177	2022-09-20 08:39:07.911089+00	2022-09-20 08:39:07.911116+00	1	t	\N	f	f
1066	PROJECT	Project	Ford Models Inc	247178	2022-09-20 08:39:07.911172+00	2022-09-20 08:39:07.911199+00	1	t	\N	f	f
1067	PROJECT	Project	Forest Grove Liquors Company	247179	2022-09-20 08:39:07.911254+00	2022-09-20 08:39:07.911281+00	1	t	\N	f	f
1068	PROJECT	Project	Formal Furnishings	247180	2022-09-20 08:39:07.911338+00	2022-09-20 08:39:07.911467+00	1	t	\N	f	f
1069	PROJECT	Project	Formisano Hardware -	247181	2022-09-20 08:39:07.911536+00	2022-09-20 08:39:07.911572+00	1	t	\N	f	f
1070	PROJECT	Project	Fort Walton Beach Electric Company	247182	2022-09-20 08:39:07.911634+00	2022-09-20 08:39:07.911663+00	1	t	\N	f	f
1071	PROJECT	Project	Fossil Watch Limited	247183	2022-09-20 08:39:07.911721+00	2022-09-20 08:39:07.911742+00	1	t	\N	f	f
1072	PROJECT	Project	Foulds Plumbing -	247184	2022-09-20 08:39:07.911809+00	2022-09-20 08:39:07.911836+00	1	t	\N	f	f
1073	PROJECT	Project	Foxe Windows Management	247185	2022-09-20 08:39:07.911892+00	2022-09-20 08:39:07.911919+00	1	t	\N	f	f
1074	PROJECT	Project	Foxmoor Formula	247186	2022-09-20 08:39:07.911975+00	2022-09-20 08:39:07.912002+00	1	t	\N	f	f
1075	PROJECT	Project	Frank Edwards	247187	2022-09-20 08:39:07.912058+00	2022-09-20 08:39:07.912085+00	1	t	\N	f	f
1076	PROJECT	Project	Frankland Attorneys Sales	247188	2022-09-20 08:39:07.912141+00	2022-09-20 08:39:07.912169+00	1	t	\N	f	f
1077	PROJECT	Project	Franklin Photography	247189	2022-09-20 08:39:07.912224+00	2022-09-20 08:39:07.912251+00	1	t	\N	f	f
1078	PROJECT	Project	Franklin Windows Inc.	247190	2022-09-20 08:39:07.912308+00	2022-09-20 08:39:07.912346+00	1	t	\N	f	f
1079	PROJECT	Project	Fredericksburg Liquors Dynamics	247191	2022-09-20 08:39:07.912518+00	2022-09-20 08:39:07.912565+00	1	t	\N	f	f
1080	PROJECT	Project	Freier Markets Incorporated	247192	2022-09-20 08:39:07.912659+00	2022-09-20 08:39:07.9127+00	1	t	\N	f	f
1081	PROJECT	Project	Freshour Apartments Agency	247193	2022-09-20 08:39:07.912762+00	2022-09-20 08:39:07.912791+00	1	t	\N	f	f
1082	PROJECT	Project	FuTech	247194	2022-09-20 08:39:07.912851+00	2022-09-20 08:39:07.912872+00	1	t	\N	f	f
1083	PROJECT	Project	Fuhrmann Lumber Manufacturing	247195	2022-09-20 08:39:07.912928+00	2022-09-20 08:39:07.912949+00	1	t	\N	f	f
1084	PROJECT	Project	Fujimura Catering Corporation	247196	2022-09-20 08:39:07.919825+00	2022-09-20 08:39:07.919867+00	1	t	\N	f	f
1085	PROJECT	Project	Fullerton Software Inc.	247197	2022-09-20 08:39:07.919935+00	2022-09-20 08:39:07.919963+00	1	t	\N	f	f
1086	PROJECT	Project	Furay and Bielawski Liquors Corporation	247198	2022-09-20 08:39:07.920023+00	2022-09-20 08:39:07.92005+00	1	t	\N	f	f
1087	PROJECT	Project	Furniture Concepts	247199	2022-09-20 08:39:07.920109+00	2022-09-20 08:39:07.920136+00	1	t	\N	f	f
1088	PROJECT	Project	Fuster Builders Co.	247200	2022-09-20 08:39:07.920193+00	2022-09-20 08:39:07.92022+00	1	t	\N	f	f
1089	PROJECT	Project	Future Office Designs	247201	2022-09-20 08:39:07.920277+00	2022-09-20 08:39:07.920304+00	1	t	\N	f	f
1090	PROJECT	Project	GProxy Online	247202	2022-09-20 08:39:07.920362+00	2022-09-20 08:39:07.920389+00	1	t	\N	f	f
1091	PROJECT	Project	Gacad Publishing Co.	247203	2022-09-20 08:39:07.920674+00	2022-09-20 08:39:07.920716+00	1	t	\N	f	f
1092	PROJECT	Project	Gadison Electric Inc.	247204	2022-09-20 08:39:07.920787+00	2022-09-20 08:39:07.920815+00	1	t	\N	f	f
1093	PROJECT	Project	Gainesville Plumbing Co.	247205	2022-09-20 08:39:07.920872+00	2022-09-20 08:39:07.920899+00	1	t	\N	f	f
1094	PROJECT	Project	Galagher Plumbing Sales	247206	2022-09-20 08:39:07.920955+00	2022-09-20 08:39:07.920982+00	1	t	\N	f	f
1095	PROJECT	Project	Galas Electric Rentals	247207	2022-09-20 08:39:07.921038+00	2022-09-20 08:39:07.921066+00	1	t	\N	f	f
1096	PROJECT	Project	Gale Custom Sailboat	247208	2022-09-20 08:39:07.921122+00	2022-09-20 08:39:07.921149+00	1	t	\N	f	f
1097	PROJECT	Project	Gallaugher Title Dynamics	247209	2022-09-20 08:39:07.921207+00	2022-09-20 08:39:07.921234+00	1	t	\N	f	f
1098	PROJECT	Project	Galvan Attorneys Systems	247210	2022-09-20 08:39:07.92129+00	2022-09-20 08:39:07.92143+00	1	t	\N	f	f
1099	PROJECT	Project	Garden Automotive Systems	247211	2022-09-20 08:39:07.921563+00	2022-09-20 08:39:07.921591+00	1	t	\N	f	f
1100	PROJECT	Project	Gardnerville Automotive Sales	247212	2022-09-20 08:39:07.921647+00	2022-09-20 08:39:07.921674+00	1	t	\N	f	f
1101	PROJECT	Project	Garitty Metal Fabricators Rentals	247213	2022-09-20 08:39:07.921731+00	2022-09-20 08:39:07.921758+00	1	t	\N	f	f
1102	PROJECT	Project	Garret Leasing Rentals	247214	2022-09-20 08:39:07.921815+00	2022-09-20 08:39:07.921842+00	1	t	\N	f	f
1103	PROJECT	Project	Gary Underwood	247215	2022-09-20 08:39:07.921898+00	2022-09-20 08:39:07.921926+00	1	t	\N	f	f
1104	PROJECT	Project	Gauch Metal Fabricators Sales	247216	2022-09-20 08:39:07.922008+00	2022-09-20 08:39:07.92203+00	1	t	\N	f	f
1105	PROJECT	Project	Gearan Title Networking	247217	2022-09-20 08:39:07.922091+00	2022-09-20 08:39:07.922121+00	1	t	\N	f	f
1106	PROJECT	Project	Genis Builders Holding Corp.	247218	2022-09-20 08:39:07.922175+00	2022-09-20 08:39:07.922308+00	1	t	\N	f	f
1107	PROJECT	Project	Gerba Construction Corporation	247219	2022-09-20 08:39:07.922375+00	2022-09-20 08:39:07.922398+00	1	t	\N	f	f
1108	PROJECT	Project	Gerney Antiques Management	247220	2022-09-20 08:39:07.922501+00	2022-09-20 08:39:07.922539+00	1	t	\N	f	f
1109	PROJECT	Project	Gesamondo Construction Leasing	247221	2022-09-20 08:39:07.922597+00	2022-09-20 08:39:07.922905+00	1	t	\N	f	f
1110	PROJECT	Project	Gettenberg Title Manufacturing	247222	2022-09-20 08:39:07.922978+00	2022-09-20 08:39:07.923002+00	1	t	\N	f	f
1111	PROJECT	Project	Gibsons Corporation	247223	2022-09-20 08:39:07.923045+00	2022-09-20 08:39:07.923056+00	1	t	\N	f	f
1112	PROJECT	Project	Gilcrease Telecom Systems	247224	2022-09-20 08:39:07.923115+00	2022-09-20 08:39:07.923142+00	1	t	\N	f	f
1113	PROJECT	Project	Gilroy Electric Services	247225	2022-09-20 08:39:07.923198+00	2022-09-20 08:39:07.923225+00	1	t	\N	f	f
1114	PROJECT	Project	Gionest Metal Fabricators Co.	247226	2022-09-20 08:39:07.9234+00	2022-09-20 08:39:07.923439+00	1	t	\N	f	f
1115	PROJECT	Project	GlassHouse Systems	247227	2022-09-20 08:39:07.923496+00	2022-09-20 08:39:07.923523+00	1	t	\N	f	f
1116	PROJECT	Project	Glish Hospital Incorporated	247228	2022-09-20 08:39:07.923578+00	2022-09-20 08:39:07.923605+00	1	t	\N	f	f
1117	PROJECT	Project	Global Supplies Inc.	247229	2022-09-20 08:39:07.923661+00	2022-09-20 08:39:07.923689+00	1	t	\N	f	f
1696	PROJECT	Project	Tim Griffin	247808	2022-09-20 08:39:09.299948+00	2022-09-20 08:39:09.299977+00	1	t	\N	f	f
1118	PROJECT	Project	Glore Apartments Distributors	247230	2022-09-20 08:39:07.923744+00	2022-09-20 08:39:07.923772+00	1	t	\N	f	f
1119	PROJECT	Project	Goepel Windows Management	247231	2022-09-20 08:39:07.923828+00	2022-09-20 08:39:07.923855+00	1	t	\N	f	f
1120	PROJECT	Project	Graber & Assoc	247232	2022-09-20 08:39:07.923911+00	2022-09-20 08:39:07.923938+00	1	t	\N	f	f
1121	PROJECT	Project	Grana Automotive and Associates	247233	2022-09-20 08:39:07.923995+00	2022-09-20 08:39:07.924022+00	1	t	\N	f	f
1122	PROJECT	Project	Grangeville Apartments Dynamics	247234	2022-09-20 08:39:07.924078+00	2022-09-20 08:39:07.924105+00	1	t	\N	f	f
1123	PROJECT	Project	Grant Electronics	247235	2022-09-20 08:39:07.924161+00	2022-09-20 08:39:07.924188+00	1	t	\N	f	f
1124	PROJECT	Project	Graphics R Us	247236	2022-09-20 08:39:07.924246+00	2022-09-20 08:39:07.924273+00	1	t	\N	f	f
1125	PROJECT	Project	Grave Apartments Sales	247237	2022-09-20 08:39:07.924329+00	2022-09-20 08:39:07.924356+00	1	t	\N	f	f
1126	PROJECT	Project	Graydon	247238	2022-09-20 08:39:07.924539+00	2022-09-20 08:39:07.924577+00	1	t	\N	f	f
1127	PROJECT	Project	Green Grocery	247239	2022-09-20 08:39:07.924634+00	2022-09-20 08:39:07.924661+00	1	t	\N	f	f
1128	PROJECT	Project	Green Street Spirits	247240	2022-09-20 08:39:07.924718+00	2022-09-20 08:39:07.924745+00	1	t	\N	f	f
1129	PROJECT	Project	Greg Muller	247241	2022-09-20 08:39:07.924801+00	2022-09-20 08:39:07.924828+00	1	t	\N	f	f
1130	PROJECT	Project	Greg Yamashige	247242	2022-09-20 08:39:07.924884+00	2022-09-20 08:39:07.924911+00	1	t	\N	f	f
1131	PROJECT	Project	Gregory Daniels	247243	2022-09-20 08:39:07.924967+00	2022-09-20 08:39:07.924994+00	1	t	\N	f	f
1132	PROJECT	Project	Gresham	247244	2022-09-20 08:39:07.925051+00	2022-09-20 08:39:07.925078+00	1	t	\N	f	f
1133	PROJECT	Project	Grines Apartments Co.	247245	2022-09-20 08:39:07.925135+00	2022-09-20 08:39:07.925162+00	1	t	\N	f	f
1134	PROJECT	Project	Guidaboni Publishing Leasing	247246	2022-09-20 08:39:07.931211+00	2022-09-20 08:39:07.931255+00	1	t	\N	f	f
1135	PROJECT	Project	Gus Lee	247247	2022-09-20 08:39:07.931324+00	2022-09-20 08:39:07.93146+00	1	t	\N	f	f
1136	PROJECT	Project	Gus Li	247248	2022-09-20 08:39:07.931542+00	2022-09-20 08:39:07.93157+00	1	t	\N	f	f
1137	PROJECT	Project	Gus Photography	247249	2022-09-20 08:39:07.931642+00	2022-09-20 08:39:07.931669+00	1	t	\N	f	f
1138	PROJECT	Project	Guzalak Leasing Leasing	247250	2022-09-20 08:39:07.931727+00	2022-09-20 08:39:07.931754+00	1	t	\N	f	f
1139	PROJECT	Project	HGH Vision	247251	2022-09-20 08:39:07.931811+00	2022-09-20 08:39:07.931838+00	1	t	\N	f	f
1140	PROJECT	Project	Hahn & Associates	247252	2022-09-20 08:39:07.931895+00	2022-09-20 08:39:07.931922+00	1	t	\N	f	f
1141	PROJECT	Project	Haleiwa Windows Leasing	247253	2022-09-20 08:39:07.931979+00	2022-09-20 08:39:07.932006+00	1	t	\N	f	f
1142	PROJECT	Project	Halick Title and Associates	247254	2022-09-20 08:39:07.932062+00	2022-09-20 08:39:07.93209+00	1	t	\N	f	f
1143	PROJECT	Project	Hambly Spirits	247255	2022-09-20 08:39:07.932146+00	2022-09-20 08:39:07.932173+00	1	t	\N	f	f
1144	PROJECT	Project	Hanninen Painting Distributors	247256	2022-09-20 08:39:07.93223+00	2022-09-20 08:39:07.932257+00	1	t	\N	f	f
1145	PROJECT	Project	Hansen Car Dealership	247257	2022-09-20 08:39:07.932314+00	2022-09-20 08:39:07.932341+00	1	t	\N	f	f
1146	PROJECT	Project	Harriage Plumbing Dynamics	247258	2022-09-20 08:39:07.932539+00	2022-09-20 08:39:07.932568+00	1	t	\N	f	f
1147	PROJECT	Project	Harriott Construction Services	247259	2022-09-20 08:39:07.932626+00	2022-09-20 08:39:07.932653+00	1	t	\N	f	f
1148	PROJECT	Project	Harrop Attorneys Inc.	247260	2022-09-20 08:39:07.93271+00	2022-09-20 08:39:07.932738+00	1	t	\N	f	f
1149	PROJECT	Project	Harting Electric Fabricators	247261	2022-09-20 08:39:07.932794+00	2022-09-20 08:39:07.932821+00	1	t	\N	f	f
1150	PROJECT	Project	Hawk Liquors Agency	247262	2022-09-20 08:39:07.932878+00	2022-09-20 08:39:07.932905+00	1	t	\N	f	f
1151	PROJECT	Project	Healy Lumber -	247263	2022-09-20 08:39:07.932962+00	2022-09-20 08:39:07.932989+00	1	t	\N	f	f
1152	PROJECT	Project	Hebden Automotive Dynamics	247264	2022-09-20 08:39:07.933046+00	2022-09-20 08:39:07.933073+00	1	t	\N	f	f
1153	PROJECT	Project	Heeralall Metal Fabricators Incorporated	247265	2022-09-20 08:39:07.93313+00	2022-09-20 08:39:07.933158+00	1	t	\N	f	f
1154	PROJECT	Project	Helfenbein Apartments Co.	247266	2022-09-20 08:39:07.933214+00	2022-09-20 08:39:07.933242+00	1	t	\N	f	f
1155	PROJECT	Project	Helferty _ Services	247267	2022-09-20 08:39:07.933299+00	2022-09-20 08:39:07.933326+00	1	t	\N	f	f
1156	PROJECT	Project	Helker and Heidkamp Software Systems	247268	2022-09-20 08:39:07.933507+00	2022-09-20 08:39:07.933546+00	1	t	\N	f	f
1157	PROJECT	Project	Helping Hands Medical Supply	247269	2022-09-20 08:39:07.933603+00	2022-09-20 08:39:07.93363+00	1	t	\N	f	f
1158	PROJECT	Project	Helvey Catering Distributors	247270	2022-09-20 08:39:07.933687+00	2022-09-20 08:39:07.933714+00	1	t	\N	f	f
1159	PROJECT	Project	Hemauer Builders Inc.	247271	2022-09-20 08:39:07.933771+00	2022-09-20 08:39:07.933798+00	1	t	\N	f	f
1160	PROJECT	Project	Hemet Builders Sales	247272	2022-09-20 08:39:07.933854+00	2022-09-20 08:39:07.933882+00	1	t	\N	f	f
1161	PROJECT	Project	Henderson Cooper	247273	2022-09-20 08:39:07.933938+00	2022-09-20 08:39:07.933965+00	1	t	\N	f	f
1162	PROJECT	Project	Henderson Liquors Manufacturing	247274	2022-09-20 08:39:07.934021+00	2022-09-20 08:39:07.934048+00	1	t	\N	f	f
1163	PROJECT	Project	Hendrikson Builders Corporation	247275	2022-09-20 08:39:07.934104+00	2022-09-20 08:39:07.934132+00	1	t	\N	f	f
1164	PROJECT	Project	Henneman Hardware	247276	2022-09-20 08:39:07.934188+00	2022-09-20 08:39:07.934216+00	1	t	\N	f	f
1165	PROJECT	Project	Herline Hospital Holding Corp.	247277	2022-09-20 08:39:07.934272+00	2022-09-20 08:39:07.9343+00	1	t	\N	f	f
1166	PROJECT	Project	Hershey's Canada	247278	2022-09-20 08:39:07.934367+00	2022-09-20 08:39:07.934522+00	1	t	\N	f	f
1167	PROJECT	Project	Hess Sundries	247279	2022-09-20 08:39:07.934568+00	2022-09-20 08:39:07.93459+00	1	t	\N	f	f
1168	PROJECT	Project	Hextall Consulting	247280	2022-09-20 08:39:07.934669+00	2022-09-20 08:39:07.934697+00	1	t	\N	f	f
1169	PROJECT	Project	Hillian Construction Fabricators	247281	2022-09-20 08:39:07.934753+00	2022-09-20 08:39:07.93478+00	1	t	\N	f	f
1170	PROJECT	Project	Hilltop Info Inc	247282	2022-09-20 08:39:07.934837+00	2022-09-20 08:39:07.934864+00	1	t	\N	f	f
1171	PROJECT	Project	Hirschy and Fahrenwald Liquors Incorporated	247283	2022-09-20 08:39:07.93492+00	2022-09-20 08:39:07.934947+00	1	t	\N	f	f
1172	PROJECT	Project	Hixson Construction Agency	247284	2022-09-20 08:39:07.935003+00	2022-09-20 08:39:07.935031+00	1	t	\N	f	f
1173	PROJECT	Project	Holgerson Automotive Services	247285	2022-09-20 08:39:07.935086+00	2022-09-20 08:39:07.935113+00	1	t	\N	f	f
1174	PROJECT	Project	Holly Romine	247286	2022-09-20 08:39:07.935169+00	2022-09-20 08:39:07.935197+00	1	t	\N	f	f
1175	PROJECT	Project	Hollyday Construction Networking	247287	2022-09-20 08:39:07.935252+00	2022-09-20 08:39:07.93528+00	1	t	\N	f	f
1176	PROJECT	Project	Holtmeier Leasing -	247288	2022-09-20 08:39:07.935452+00	2022-09-20 08:39:07.9355+00	1	t	\N	f	f
1177	PROJECT	Project	Honie Hospital Systems	247289	2022-09-20 08:39:07.93556+00	2022-09-20 08:39:07.935587+00	1	t	\N	f	f
1178	PROJECT	Project	Honolulu Attorneys Sales	247290	2022-09-20 08:39:07.935644+00	2022-09-20 08:39:07.935671+00	1	t	\N	f	f
1179	PROJECT	Project	Honolulu Markets Group	247291	2022-09-20 08:39:07.935727+00	2022-09-20 08:39:07.935754+00	1	t	\N	f	f
1180	PROJECT	Project	Hood River Telecom	247292	2022-09-20 08:39:07.93581+00	2022-09-20 08:39:07.935837+00	1	t	\N	f	f
1181	PROJECT	Project	Huck Apartments Inc.	247293	2022-09-20 08:39:07.935894+00	2022-09-20 08:39:07.935921+00	1	t	\N	f	f
1182	PROJECT	Project	Hughson Runners	247294	2022-09-20 08:39:07.935978+00	2022-09-20 08:39:07.936005+00	1	t	\N	f	f
1183	PROJECT	Project	Huit and Duer Publishing Dynamics	247295	2022-09-20 08:39:07.936061+00	2022-09-20 08:39:07.936088+00	1	t	\N	f	f
1184	PROJECT	Project	Humphrey Yogurt	247296	2022-09-20 08:39:07.943889+00	2022-09-20 08:39:07.943929+00	1	t	\N	f	f
1185	PROJECT	Project	Huntsville Apartments and Associates	247297	2022-09-20 08:39:07.943988+00	2022-09-20 08:39:07.944016+00	1	t	\N	f	f
1186	PROJECT	Project	Hurlbutt Markets -	247298	2022-09-20 08:39:07.944073+00	2022-09-20 08:39:07.9441+00	1	t	\N	f	f
1187	PROJECT	Project	Hurtgen Hospital Manufacturing	247299	2022-09-20 08:39:07.944157+00	2022-09-20 08:39:07.944184+00	1	t	\N	f	f
1188	PROJECT	Project	IBA Enterprises Inc	247300	2022-09-20 08:39:07.94424+00	2022-09-20 08:39:07.944267+00	1	t	\N	f	f
1189	PROJECT	Project	ICC Inc	247301	2022-09-20 08:39:07.944323+00	2022-09-20 08:39:07.94435+00	1	t	\N	f	f
1191	PROJECT	Project	Imperial Liquors Distributors	247303	2022-09-20 08:39:07.944629+00	2022-09-20 08:39:07.944656+00	1	t	\N	f	f
1192	PROJECT	Project	Imran Kahn	247304	2022-09-20 08:39:07.944712+00	2022-09-20 08:39:07.94474+00	1	t	\N	f	f
1193	PROJECT	Project	Indianapolis Liquors Rentals	247305	2022-09-20 08:39:07.944796+00	2022-09-20 08:39:07.944823+00	1	t	\N	f	f
1194	PROJECT	Project	Installation 2	247306	2022-09-20 08:39:07.944879+00	2022-09-20 08:39:07.944906+00	1	t	\N	f	f
1195	PROJECT	Project	Installation FP	247307	2022-09-20 08:39:07.944962+00	2022-09-20 08:39:07.944989+00	1	t	\N	f	f
1196	PROJECT	Project	Integrys Ltd	247308	2022-09-20 08:39:07.945045+00	2022-09-20 08:39:07.945073+00	1	t	\N	f	f
1197	PROJECT	Project	InterWorks Ltd	247309	2022-09-20 08:39:07.945128+00	2022-09-20 08:39:07.945156+00	1	t	\N	f	f
1198	PROJECT	Project	Interior Solutions	247310	2022-09-20 08:39:07.945212+00	2022-09-20 08:39:07.945239+00	1	t	\N	f	f
1199	PROJECT	Project	Iorio Lumber Incorporated	247311	2022-09-20 08:39:07.945295+00	2022-09-20 08:39:07.945323+00	1	t	\N	f	f
1200	PROJECT	Project	JKL Co.	247312	2022-09-20 08:39:07.945466+00	2022-09-20 08:39:07.945494+00	1	t	\N	f	f
1201	PROJECT	Project	Jackie Kugan	247313	2022-09-20 08:39:07.945564+00	2022-09-20 08:39:07.945593+00	1	t	\N	f	f
1202	PROJECT	Project	Jackson Alexander	247314	2022-09-20 08:39:07.945662+00	2022-09-20 08:39:07.945688+00	1	t	\N	f	f
1203	PROJECT	Project	Jaenicke Builders Management	247315	2022-09-20 08:39:07.945731+00	2022-09-20 08:39:07.945751+00	1	t	\N	f	f
1204	PROJECT	Project	Jake Hamilton	247316	2022-09-20 08:39:07.945812+00	2022-09-20 08:39:07.945841+00	1	t	\N	f	f
1205	PROJECT	Project	James McClure	247317	2022-09-20 08:39:07.9459+00	2022-09-20 08:39:07.945939+00	1	t	\N	f	f
1206	PROJECT	Project	Jamie Taylor	247318	2022-09-20 08:39:07.945995+00	2022-09-20 08:39:07.946023+00	1	t	\N	f	f
1207	PROJECT	Project	Janiak Attorneys Inc.	247319	2022-09-20 08:39:07.946078+00	2022-09-20 08:39:07.946105+00	1	t	\N	f	f
1208	PROJECT	Project	Jasmer Antiques Management	247320	2022-09-20 08:39:07.946162+00	2022-09-20 08:39:07.946189+00	1	t	\N	f	f
1209	PROJECT	Project	Jason Jacob	247321	2022-09-20 08:39:07.946245+00	2022-09-20 08:39:07.946283+00	1	t	\N	f	f
1210	PROJECT	Project	Jason Paul Distribution	247322	2022-09-20 08:39:07.946432+00	2022-09-20 08:39:07.946461+00	1	t	\N	f	f
1211	PROJECT	Project	Jeff Campbell	247323	2022-09-20 08:39:07.946529+00	2022-09-20 08:39:07.946697+00	1	t	\N	f	f
1212	PROJECT	Project	Jelle Catering Group	247324	2022-09-20 08:39:07.946897+00	2022-09-20 08:39:07.946928+00	1	t	\N	f	f
1213	PROJECT	Project	Jennings Financial	247325	2022-09-20 08:39:07.947107+00	2022-09-20 08:39:07.947478+00	1	t	\N	f	f
1214	PROJECT	Project	Jennings Financial Inc.	247326	2022-09-20 08:39:07.947679+00	2022-09-20 08:39:07.947707+00	1	t	\N	f	f
1215	PROJECT	Project	Jeune Antiques Group	247327	2022-09-20 08:39:07.947765+00	2022-09-20 08:39:07.947792+00	1	t	\N	f	f
1216	PROJECT	Project	Jeziorski _ Dynamics	247328	2022-09-20 08:39:07.947849+00	2022-09-20 08:39:07.947876+00	1	t	\N	f	f
1217	PROJECT	Project	Jim Strong	247329	2022-09-20 08:39:07.947932+00	2022-09-20 08:39:07.947959+00	1	t	\N	f	f
1218	PROJECT	Project	Jim's Custom Frames	247330	2022-09-20 08:39:07.948016+00	2022-09-20 08:39:07.948043+00	1	t	\N	f	f
1219	PROJECT	Project	Joanne Miller	247331	2022-09-20 08:39:07.948099+00	2022-09-20 08:39:07.948126+00	1	t	\N	f	f
1220	PROJECT	Project	Joe Smith	247332	2022-09-20 08:39:07.948183+00	2022-09-20 08:39:07.94821+00	1	t	\N	f	f
1221	PROJECT	Project	Johar Software Corporation	247333	2022-09-20 08:39:07.948266+00	2022-09-20 08:39:07.948293+00	1	t	\N	f	f
1222	PROJECT	Project	John Boba	247334	2022-09-20 08:39:07.948481+00	2022-09-20 08:39:07.948521+00	1	t	\N	f	f
1223	PROJECT	Project	John G. Roche Opticians	247335	2022-09-20 08:39:07.948578+00	2022-09-20 08:39:07.948606+00	1	t	\N	f	f
1224	PROJECT	Project	John Nguyen	247336	2022-09-20 08:39:07.948662+00	2022-09-20 08:39:07.948689+00	1	t	\N	f	f
1225	PROJECT	Project	John Paulsen	247337	2022-09-20 08:39:07.948745+00	2022-09-20 08:39:07.948772+00	1	t	\N	f	f
1226	PROJECT	Project	John Smith Home Design	247338	2022-09-20 08:39:07.948828+00	2022-09-20 08:39:07.948855+00	1	t	\N	f	f
1227	PROJECT	Project	Johnson & Johnson	247339	2022-09-20 08:39:07.948911+00	2022-09-20 08:39:07.948938+00	1	t	\N	f	f
1228	PROJECT	Project	Jonas Island Applied Radiation	247340	2022-09-20 08:39:07.948995+00	2022-09-20 08:39:07.949022+00	1	t	\N	f	f
1229	PROJECT	Project	Jonathan Ketner	247341	2022-09-20 08:39:07.949078+00	2022-09-20 08:39:07.949105+00	1	t	\N	f	f
1230	PROJECT	Project	Jones & Bernstein Law Firm	247342	2022-09-20 08:39:07.949161+00	2022-09-20 08:39:07.949188+00	1	t	\N	f	f
1231	PROJECT	Project	Julia Daniels	247343	2022-09-20 08:39:07.949245+00	2022-09-20 08:39:07.949272+00	1	t	\N	f	f
1232	PROJECT	Project	Julie Frankel	247344	2022-09-20 08:39:07.949328+00	2022-09-20 08:39:07.949366+00	1	t	\N	f	f
1233	PROJECT	Project	Juno Gold Wines	247345	2022-09-20 08:39:07.949545+00	2022-09-20 08:39:07.949573+00	1	t	\N	f	f
1234	PROJECT	Project	Justin Hartman	247346	2022-09-20 08:39:08.382899+00	2022-09-20 08:39:08.382953+00	1	t	\N	f	f
1235	PROJECT	Project	Justin Ramos	247347	2022-09-20 08:39:08.383014+00	2022-09-20 08:39:08.383042+00	1	t	\N	f	f
1236	PROJECT	Project	KEM Corporation	247348	2022-09-20 08:39:08.3831+00	2022-09-20 08:39:08.383128+00	1	t	\N	f	f
1237	PROJECT	Project	Kababik and Ramariz Liquors Corporation	247349	2022-09-20 08:39:08.383185+00	2022-09-20 08:39:08.383213+00	1	t	\N	f	f
1238	PROJECT	Project	Kalfa Painting Holding Corp.	247350	2022-09-20 08:39:08.38327+00	2022-09-20 08:39:08.383297+00	1	t	\N	f	f
1239	PROJECT	Project	Kalinsky Consulting Group	247351	2022-09-20 08:39:08.383369+00	2022-09-20 08:39:08.383512+00	1	t	\N	f	f
1240	PROJECT	Project	Kalisch Lumber Group	247352	2022-09-20 08:39:08.383581+00	2022-09-20 08:39:08.383609+00	1	t	\N	f	f
1241	PROJECT	Project	Kallmeyer Antiques Dynamics	247353	2022-09-20 08:39:08.383667+00	2022-09-20 08:39:08.383694+00	1	t	\N	f	f
1242	PROJECT	Project	Kamps Electric Systems	247354	2022-09-20 08:39:08.383752+00	2022-09-20 08:39:08.383779+00	1	t	\N	f	f
1243	PROJECT	Project	Kara's Cafe	247355	2022-09-20 08:39:08.383849+00	2022-09-20 08:39:08.383878+00	1	t	\N	f	f
1244	PROJECT	Project	Kate Winters	247356	2022-09-20 08:39:08.383939+00	2022-09-20 08:39:08.383968+00	1	t	\N	f	f
1245	PROJECT	Project	Katie Fischer	247357	2022-09-20 08:39:08.384029+00	2022-09-20 08:39:08.384068+00	1	t	\N	f	f
1246	PROJECT	Project	Kavadias Construction Sales	247358	2022-09-20 08:39:08.384126+00	2022-09-20 08:39:08.384153+00	1	t	\N	f	f
1247	PROJECT	Project	Kavanagh Brothers	247359	2022-09-20 08:39:08.384209+00	2022-09-20 08:39:08.384237+00	1	t	\N	f	f
1248	PROJECT	Project	Kavanaugh Real Estate	247360	2022-09-20 08:39:08.384294+00	2022-09-20 08:39:08.384321+00	1	t	\N	f	f
1249	PROJECT	Project	Keblish Catering Distributors	247361	2022-09-20 08:39:08.384485+00	2022-09-20 08:39:08.384515+00	1	t	\N	f	f
1250	PROJECT	Project	Kelleher Title Services	247362	2022-09-20 08:39:08.384584+00	2022-09-20 08:39:08.384612+00	1	t	\N	f	f
1251	PROJECT	Project	Kemme Builders Management	247363	2022-09-20 08:39:08.384669+00	2022-09-20 08:39:08.384697+00	1	t	\N	f	f
1252	PROJECT	Project	Kempker Title Manufacturing	247364	2022-09-20 08:39:08.384754+00	2022-09-20 08:39:08.384782+00	1	t	\N	f	f
1253	PROJECT	Project	Ken Chua	247365	2022-09-20 08:39:08.384839+00	2022-09-20 08:39:08.384866+00	1	t	\N	f	f
1254	PROJECT	Project	Kenney Windows Dynamics	247366	2022-09-20 08:39:08.384923+00	2022-09-20 08:39:08.384951+00	1	t	\N	f	f
1255	PROJECT	Project	Kerekes Lumber Networking	247367	2022-09-20 08:39:08.385008+00	2022-09-20 08:39:08.385036+00	1	t	\N	f	f
1256	PROJECT	Project	Kerfien Title Company	247368	2022-09-20 08:39:08.385093+00	2022-09-20 08:39:08.38512+00	1	t	\N	f	f
1257	PROJECT	Project	Kerry Furnishings & Design	247369	2022-09-20 08:39:08.385177+00	2022-09-20 08:39:08.385204+00	1	t	\N	f	f
1258	PROJECT	Project	Kevin Smith	247370	2022-09-20 08:39:08.385261+00	2022-09-20 08:39:08.385289+00	1	t	\N	f	f
1259	PROJECT	Project	Kiedrowski Telecom Services	247371	2022-09-20 08:39:08.385346+00	2022-09-20 08:39:08.385495+00	1	t	\N	f	f
1260	PROJECT	Project	Kieff Software Fabricators	247372	2022-09-20 08:39:08.385561+00	2022-09-20 08:39:08.385602+00	1	t	\N	f	f
1261	PROJECT	Project	Killian Construction Networking	247373	2022-09-20 08:39:08.385683+00	2022-09-20 08:39:08.385711+00	1	t	\N	f	f
1262	PROJECT	Project	Kim Wilson	247374	2022-09-20 08:39:08.385767+00	2022-09-20 08:39:08.385795+00	1	t	\N	f	f
1263	PROJECT	Project	Kingman Antiques Corporation	247375	2022-09-20 08:39:08.385852+00	2022-09-20 08:39:08.385879+00	1	t	\N	f	f
1264	PROJECT	Project	Kino Inc	247376	2022-09-20 08:39:08.385936+00	2022-09-20 08:39:08.385963+00	1	t	\N	f	f
1265	PROJECT	Project	Kirkville Builders -	247377	2022-09-20 08:39:08.38602+00	2022-09-20 08:39:08.386047+00	1	t	\N	f	f
1266	PROJECT	Project	Kittel Hardware Dynamics	247378	2022-09-20 08:39:08.386104+00	2022-09-20 08:39:08.386131+00	1	t	\N	f	f
1267	PROJECT	Project	Knoop Telecom Agency	247379	2022-09-20 08:39:08.386187+00	2022-09-20 08:39:08.386215+00	1	t	\N	f	f
1268	PROJECT	Project	Knotek Hospital Company	247380	2022-09-20 08:39:08.386271+00	2022-09-20 08:39:08.386298+00	1	t	\N	f	f
1269	PROJECT	Project	Konecny Markets Co.	247381	2022-09-20 08:39:08.386366+00	2022-09-20 08:39:08.386503+00	1	t	\N	f	f
1270	PROJECT	Project	Koshi Metal Fabricators Corporation	247382	2022-09-20 08:39:08.386573+00	2022-09-20 08:39:08.3866+00	1	t	\N	f	f
1271	PROJECT	Project	Kovats Publishing	247383	2022-09-20 08:39:08.386657+00	2022-09-20 08:39:08.386684+00	1	t	\N	f	f
1272	PROJECT	Project	Kramer Construction	247384	2022-09-20 08:39:08.386741+00	2022-09-20 08:39:08.386769+00	1	t	\N	f	f
1273	PROJECT	Project	Krista Thomas Recruiting	247385	2022-09-20 08:39:08.386825+00	2022-09-20 08:39:08.386853+00	1	t	\N	f	f
1274	PROJECT	Project	Kristen Welch	247386	2022-09-20 08:39:08.386909+00	2022-09-20 08:39:08.386937+00	1	t	\N	f	f
1275	PROJECT	Project	Kroetz Electric Dynamics	247387	2022-09-20 08:39:08.386994+00	2022-09-20 08:39:08.387021+00	1	t	\N	f	f
1276	PROJECT	Project	Kugan Autodesk Inc	247388	2022-09-20 08:39:08.387078+00	2022-09-20 08:39:08.387105+00	1	t	\N	f	f
1277	PROJECT	Project	Kunstlinger Automotive Manufacturing	247389	2022-09-20 08:39:08.387162+00	2022-09-20 08:39:08.38719+00	1	t	\N	f	f
1278	PROJECT	Project	Kyle Keosian	247390	2022-09-20 08:39:08.387246+00	2022-09-20 08:39:08.387273+00	1	t	\N	f	f
1279	PROJECT	Project	La Grande Liquors Dynamics	247391	2022-09-20 08:39:08.38733+00	2022-09-20 08:39:08.387368+00	1	t	\N	f	f
1280	PROJECT	Project	Labarba Markets Corporation	247392	2022-09-20 08:39:08.387544+00	2022-09-20 08:39:08.387571+00	1	t	\N	f	f
1281	PROJECT	Project	Laditka and Ceppetelli Publishing Holding Corp.	247393	2022-09-20 08:39:08.387629+00	2022-09-20 08:39:08.387656+00	1	t	\N	f	f
1282	PROJECT	Project	Lafayette Hardware Services	247394	2022-09-20 08:39:08.387713+00	2022-09-20 08:39:08.38774+00	1	t	\N	f	f
1283	PROJECT	Project	Lafayette Metal Fabricators Rentals	247395	2022-09-20 08:39:08.387797+00	2022-09-20 08:39:08.387824+00	1	t	\N	f	f
1284	PROJECT	Project	Lake Worth Markets Fabricators	247396	2022-09-20 08:39:08.395007+00	2022-09-20 08:39:08.395045+00	1	t	\N	f	f
1285	PROJECT	Project	Lakeside Inc	247397	2022-09-20 08:39:08.395106+00	2022-09-20 08:39:08.395133+00	1	t	\N	f	f
1286	PROJECT	Project	Lancaster Liquors Inc.	247398	2022-09-20 08:39:08.39519+00	2022-09-20 08:39:08.395217+00	1	t	\N	f	f
1287	PROJECT	Project	Lanning and Urraca Construction Corporation	247399	2022-09-20 08:39:08.395274+00	2022-09-20 08:39:08.395301+00	1	t	\N	f	f
1288	PROJECT	Project	Laramie Construction Co.	247400	2022-09-20 08:39:08.395358+00	2022-09-20 08:39:08.395482+00	1	t	\N	f	f
1289	PROJECT	Project	Largo Lumber Co.	247401	2022-09-20 08:39:08.395552+00	2022-09-20 08:39:08.39558+00	1	t	\N	f	f
1290	PROJECT	Project	Lariosa Lumber Corporation	247402	2022-09-20 08:39:08.395637+00	2022-09-20 08:39:08.395665+00	1	t	\N	f	f
1291	PROJECT	Project	Las Vegas Electric Manufacturing	247403	2022-09-20 08:39:08.395721+00	2022-09-20 08:39:08.395749+00	1	t	\N	f	f
1292	PROJECT	Project	Laser Images Inc.	247404	2022-09-20 08:39:08.395805+00	2022-09-20 08:39:08.395832+00	1	t	\N	f	f
1293	PROJECT	Project	Lawley and Barends Painting Distributors	247405	2022-09-20 08:39:08.395889+00	2022-09-20 08:39:08.395916+00	1	t	\N	f	f
1294	PROJECT	Project	Lead 154	247406	2022-09-20 08:39:08.395972+00	2022-09-20 08:39:08.395999+00	1	t	\N	f	f
1295	PROJECT	Project	Lead 155	247407	2022-09-20 08:39:08.396055+00	2022-09-20 08:39:08.396082+00	1	t	\N	f	f
1296	PROJECT	Project	Leemans Builders Agency	247408	2022-09-20 08:39:08.39615+00	2022-09-20 08:39:08.39618+00	1	t	\N	f	f
1297	PROJECT	Project	Lenza and Lanzoni Plumbing Co.	247409	2022-09-20 08:39:08.39624+00	2022-09-20 08:39:08.396269+00	1	t	\N	f	f
1298	PROJECT	Project	Levitan Plumbing Dynamics	247410	2022-09-20 08:39:08.396329+00	2022-09-20 08:39:08.396359+00	1	t	\N	f	f
1299	PROJECT	Project	Lexington Hospital Sales	247411	2022-09-20 08:39:08.396562+00	2022-09-20 08:39:08.396592+00	1	t	\N	f	f
1300	PROJECT	Project	Liechti Lumber Sales	247412	2022-09-20 08:39:08.39666+00	2022-09-20 08:39:08.397102+00	1	t	\N	f	f
1301	PROJECT	Project	Lillian Thurham	247413	2022-09-20 08:39:08.397298+00	2022-09-20 08:39:08.397327+00	1	t	\N	f	f
1302	PROJECT	Project	Limbo Leasing Leasing	247414	2022-09-20 08:39:08.397397+00	2022-09-20 08:39:08.397424+00	1	t	\N	f	f
1303	PROJECT	Project	Lina's Dance Studio	247415	2022-09-20 08:39:08.397482+00	2022-09-20 08:39:08.397509+00	1	t	\N	f	f
1304	PROJECT	Project	Linberg Windows Agency	247416	2022-09-20 08:39:08.397566+00	2022-09-20 08:39:08.397593+00	1	t	\N	f	f
1305	PROJECT	Project	Linder Windows Rentals	247417	2022-09-20 08:39:08.39765+00	2022-09-20 08:39:08.397677+00	1	t	\N	f	f
1306	PROJECT	Project	Linderman Builders Agency	247418	2022-09-20 08:39:08.397733+00	2022-09-20 08:39:08.397761+00	1	t	\N	f	f
1307	PROJECT	Project	Lindman and Kastens Antiques -	247419	2022-09-20 08:39:08.397817+00	2022-09-20 08:39:08.397844+00	1	t	\N	f	f
1308	PROJECT	Project	Linear International Footwear	247420	2022-09-20 08:39:08.3979+00	2022-09-20 08:39:08.397928+00	1	t	\N	f	f
1309	PROJECT	Project	Lintex Group	247421	2022-09-20 08:39:08.397984+00	2022-09-20 08:39:08.398011+00	1	t	\N	f	f
1310	PROJECT	Project	Lisa Fiore	247422	2022-09-20 08:39:08.398068+00	2022-09-20 08:39:08.398095+00	1	t	\N	f	f
1311	PROJECT	Project	Lisa Wilson	247423	2022-09-20 08:39:08.398152+00	2022-09-20 08:39:08.398179+00	1	t	\N	f	f
1312	PROJECT	Project	Liverpool Hospital Leasing	247424	2022-09-20 08:39:08.398236+00	2022-09-20 08:39:08.398263+00	1	t	\N	f	f
1313	PROJECT	Project	Lizarrago Markets Corporation	247425	2022-09-20 08:39:08.398319+00	2022-09-20 08:39:08.398346+00	1	t	\N	f	f
1314	PROJECT	Project	Lobby Remodel	247426	2022-09-20 08:39:08.398403+00	2022-09-20 08:39:08.398561+00	1	t	\N	f	f
1315	PROJECT	Project	Lodato Painting and Associates	247427	2022-09-20 08:39:08.398632+00	2022-09-20 08:39:08.39866+00	1	t	\N	f	f
1316	PROJECT	Project	Loeza Catering Agency	247428	2022-09-20 08:39:08.398717+00	2022-09-20 08:39:08.398745+00	1	t	\N	f	f
1317	PROJECT	Project	Lois Automotive Agency	247429	2022-09-20 08:39:08.398801+00	2022-09-20 08:39:08.398828+00	1	t	\N	f	f
1318	PROJECT	Project	Lomax Transportation	247430	2022-09-20 08:39:08.398885+00	2022-09-20 08:39:08.398912+00	1	t	\N	f	f
1319	PROJECT	Project	Lompoc _ Systems	247431	2022-09-20 08:39:08.398969+00	2022-09-20 08:39:08.398996+00	1	t	\N	f	f
1320	PROJECT	Project	Lonabaugh Markets Distributors	247432	2022-09-20 08:39:08.399053+00	2022-09-20 08:39:08.39908+00	1	t	\N	f	f
1321	PROJECT	Project	Lorandeau Builders Holding Corp.	247433	2022-09-20 08:39:08.399137+00	2022-09-20 08:39:08.399164+00	1	t	\N	f	f
1322	PROJECT	Project	Lou Baus	247434	2022-09-20 08:39:08.39922+00	2022-09-20 08:39:08.399248+00	1	t	\N	f	f
1323	PROJECT	Project	Louis Fabre	247435	2022-09-20 08:39:08.399304+00	2022-09-20 08:39:08.399342+00	1	t	\N	f	f
1324	PROJECT	Project	Loven and Frothingham Hardware Distributors	247436	2022-09-20 08:39:08.399523+00	2022-09-20 08:39:08.399551+00	1	t	\N	f	f
1325	PROJECT	Project	Lucic and Perfect Publishing Systems	247437	2022-09-20 08:39:08.399607+00	2022-09-20 08:39:08.399634+00	1	t	\N	f	f
1326	PROJECT	Project	Lucie Hospital Group	247438	2022-09-20 08:39:08.399691+00	2022-09-20 08:39:08.399718+00	1	t	\N	f	f
1327	PROJECT	Project	Luffy Apartments Company	247439	2022-09-20 08:39:08.399786+00	2022-09-20 08:39:08.399998+00	1	t	\N	f	f
1328	PROJECT	Project	Luigi Imports	247440	2022-09-20 08:39:08.400057+00	2022-09-20 08:39:08.400084+00	1	t	\N	f	f
1329	PROJECT	Project	Lummus Telecom Rentals	247441	2022-09-20 08:39:08.400141+00	2022-09-20 08:39:08.400169+00	1	t	\N	f	f
1330	PROJECT	Project	Lurtz Painting Co.	247442	2022-09-20 08:39:08.400225+00	2022-09-20 08:39:08.400263+00	1	t	\N	f	f
1331	PROJECT	Project	Lyas Builders Inc.	247443	2022-09-20 08:39:08.400443+00	2022-09-20 08:39:08.400471+00	1	t	\N	f	f
1332	PROJECT	Project	MAC	247444	2022-09-20 08:39:08.400528+00	2022-09-20 08:39:08.400555+00	1	t	\N	f	f
1333	PROJECT	Project	MPower	247445	2022-09-20 08:39:08.400612+00	2022-09-20 08:39:08.400639+00	1	t	\N	f	f
1334	PROJECT	Project	MW International (CAD)	247446	2022-09-20 08:39:08.406643+00	2022-09-20 08:39:08.406685+00	1	t	\N	f	f
1335	PROJECT	Project	Mackenzie Corporation	247447	2022-09-20 08:39:08.406751+00	2022-09-20 08:39:08.40678+00	1	t	\N	f	f
1336	PROJECT	Project	Mackie Painting Company	247448	2022-09-20 08:39:08.406841+00	2022-09-20 08:39:08.406869+00	1	t	\N	f	f
1337	PROJECT	Project	Malena Construction Fabricators	247449	2022-09-20 08:39:08.406928+00	2022-09-20 08:39:08.406955+00	1	t	\N	f	f
1338	PROJECT	Project	Maleonado Publishing Company	247450	2022-09-20 08:39:08.407013+00	2022-09-20 08:39:08.407041+00	1	t	\N	f	f
1339	PROJECT	Project	Mandos	247451	2022-09-20 08:39:08.407477+00	2022-09-20 08:39:08.40781+00	1	t	\N	f	f
1340	PROJECT	Project	Manivong Apartments Incorporated	247452	2022-09-20 08:39:08.407872+00	2022-09-20 08:39:08.4079+00	1	t	\N	f	f
1341	PROJECT	Project	Manwarren Markets Holding Corp.	247453	2022-09-20 08:39:08.40796+00	2022-09-20 08:39:08.407987+00	1	t	\N	f	f
1342	PROJECT	Project	Maple Leaf Foods	247454	2022-09-20 08:39:08.408045+00	2022-09-20 08:39:08.408072+00	1	t	\N	f	f
1343	PROJECT	Project	Marabella Title Agency	247455	2022-09-20 08:39:08.40813+00	2022-09-20 08:39:08.408158+00	1	t	\N	f	f
1344	PROJECT	Project	Marietta Title Co.	247456	2022-09-20 08:39:08.408215+00	2022-09-20 08:39:08.408242+00	1	t	\N	f	f
1345	PROJECT	Project	Marionneaux Catering Incorporated	247457	2022-09-20 08:39:08.408299+00	2022-09-20 08:39:08.408337+00	1	t	\N	f	f
1346	PROJECT	Project	Mark's Sporting Goods	247458	2022-09-20 08:39:08.408504+00	2022-09-20 08:39:08.408529+00	1	t	\N	f	f
1347	PROJECT	Project	Markewich Builders Rentals	247459	2022-09-20 08:39:08.408601+00	2022-09-20 08:39:08.408628+00	1	t	\N	f	f
1348	PROJECT	Project	Marrello Software Services	247460	2022-09-20 08:39:08.408686+00	2022-09-20 08:39:08.408713+00	1	t	\N	f	f
1349	PROJECT	Project	Marston Hardware -	247461	2022-09-20 08:39:08.40877+00	2022-09-20 08:39:08.408797+00	1	t	\N	f	f
1350	PROJECT	Project	Martin Gelina	247462	2022-09-20 08:39:08.408855+00	2022-09-20 08:39:08.408882+00	1	t	\N	f	f
1351	PROJECT	Project	Mason's Travel Services	247463	2022-09-20 08:39:08.408939+00	2022-09-20 08:39:08.408966+00	1	t	\N	f	f
1352	PROJECT	Project	Matsuzaki Builders Services	247464	2022-09-20 08:39:08.409023+00	2022-09-20 08:39:08.40905+00	1	t	\N	f	f
1353	PROJECT	Project	Matthew Davison	247465	2022-09-20 08:39:08.409106+00	2022-09-20 08:39:08.409133+00	1	t	\N	f	f
1354	PROJECT	Project	Matzke Title Co.	247466	2022-09-20 08:39:08.40919+00	2022-09-20 08:39:08.409216+00	1	t	\N	f	f
1355	PROJECT	Project	Maxx Corner Market	247467	2022-09-20 08:39:08.409273+00	2022-09-20 08:39:08.4093+00	1	t	\N	f	f
1356	PROJECT	Project	McEdwards & Whitwell	247468	2022-09-20 08:39:08.409371+00	2022-09-20 08:39:08.409494+00	1	t	\N	f	f
1357	PROJECT	Project	McKay Financial	247469	2022-09-20 08:39:08.409569+00	2022-09-20 08:39:08.409596+00	1	t	\N	f	f
1358	PROJECT	Project	Mcburnie Hardware Dynamics	247470	2022-09-20 08:39:08.409653+00	2022-09-20 08:39:08.40968+00	1	t	\N	f	f
1359	PROJECT	Project	Mcdorman Software Holding Corp.	247471	2022-09-20 08:39:08.409737+00	2022-09-20 08:39:08.409764+00	1	t	\N	f	f
1360	PROJECT	Project	Mcelderry Apartments Systems	247472	2022-09-20 08:39:08.40982+00	2022-09-20 08:39:08.409847+00	1	t	\N	f	f
1361	PROJECT	Project	Mcguff and Spriggins Hospital Group	247473	2022-09-20 08:39:08.410119+00	2022-09-20 08:39:08.410153+00	1	t	\N	f	f
1362	PROJECT	Project	Mcoy and Donlin Attorneys Sales	247474	2022-09-20 08:39:08.410213+00	2022-09-20 08:39:08.410453+00	1	t	\N	f	f
1363	PROJECT	Project	Medcan Mgmt Inc	247475	2022-09-20 08:39:08.410686+00	2022-09-20 08:39:08.410881+00	1	t	\N	f	f
1364	PROJECT	Project	Medved	247476	2022-09-20 08:39:08.411072+00	2022-09-20 08:39:08.4111+00	1	t	\N	f	f
1365	PROJECT	Project	Megaloid labs	247477	2022-09-20 08:39:08.411535+00	2022-09-20 08:39:08.411563+00	1	t	\N	f	f
1366	PROJECT	Project	Meisner Software Inc.	247478	2022-09-20 08:39:08.411621+00	2022-09-20 08:39:08.411649+00	1	t	\N	f	f
1367	PROJECT	Project	Mele Plumbing Manufacturing	247479	2022-09-20 08:39:08.411705+00	2022-09-20 08:39:08.411732+00	1	t	\N	f	f
1368	PROJECT	Project	Melissa Wine Shop	247480	2022-09-20 08:39:08.411788+00	2022-09-20 08:39:08.411816+00	1	t	\N	f	f
1369	PROJECT	Project	Melville Painting Rentals	247481	2022-09-20 08:39:08.411872+00	2022-09-20 08:39:08.411899+00	1	t	\N	f	f
1370	PROJECT	Project	Meneses Telecom Corporation	247482	2022-09-20 08:39:08.411955+00	2022-09-20 08:39:08.411983+00	1	t	\N	f	f
1371	PROJECT	Project	Mentor Graphics	247483	2022-09-20 08:39:08.412039+00	2022-09-20 08:39:08.412067+00	1	t	\N	f	f
1372	PROJECT	Project	Micehl Bertrand	247484	2022-09-20 08:39:08.412123+00	2022-09-20 08:39:08.41215+00	1	t	\N	f	f
1373	PROJECT	Project	Michael Jannsen	247485	2022-09-20 08:39:08.412206+00	2022-09-20 08:39:08.412233+00	1	t	\N	f	f
1374	PROJECT	Project	Michael Spencer	247486	2022-09-20 08:39:08.41229+00	2022-09-20 08:39:08.412317+00	1	t	\N	f	f
1375	PROJECT	Project	Michael Wakefield	247487	2022-09-20 08:39:08.412374+00	2022-09-20 08:39:08.412412+00	1	t	\N	f	f
1376	PROJECT	Project	Microskills	247488	2022-09-20 08:39:08.412591+00	2022-09-20 08:39:08.412619+00	1	t	\N	f	f
1377	PROJECT	Project	Midgette Markets	247489	2022-09-20 08:39:08.412676+00	2022-09-20 08:39:08.412704+00	1	t	\N	f	f
1378	PROJECT	Project	Mike Dee	247490	2022-09-20 08:39:08.41276+00	2022-09-20 08:39:08.412787+00	1	t	\N	f	f
1379	PROJECT	Project	Mike Franko	247491	2022-09-20 08:39:08.412843+00	2022-09-20 08:39:08.412871+00	1	t	\N	f	f
1380	PROJECT	Project	Mike Miller	247492	2022-09-20 08:39:08.412927+00	2022-09-20 08:39:08.412954+00	1	t	\N	f	f
1381	PROJECT	Project	Millenium Engineering	247493	2022-09-20 08:39:08.413012+00	2022-09-20 08:39:08.41304+00	1	t	\N	f	f
1382	PROJECT	Project	Miller's Dry Cleaning	247494	2022-09-20 08:39:08.413096+00	2022-09-20 08:39:08.413124+00	1	t	\N	f	f
1383	PROJECT	Project	Mindy Peiris	247495	2022-09-20 08:39:08.41318+00	2022-09-20 08:39:08.413207+00	1	t	\N	f	f
1384	PROJECT	Project	Mineral Painting Inc.	247496	2022-09-20 08:39:08.421222+00	2022-09-20 08:39:08.421275+00	1	t	\N	f	f
1385	PROJECT	Project	Miquel Apartments Leasing	247497	2022-09-20 08:39:08.421643+00	2022-09-20 08:39:08.421807+00	1	t	\N	f	f
1386	PROJECT	Project	Mission Liquors	247498	2022-09-20 08:39:08.422556+00	2022-09-20 08:39:08.422605+00	1	t	\N	f	f
1387	PROJECT	Project	Mitani Hardware Company	247499	2022-09-20 08:39:08.42269+00	2022-09-20 08:39:08.422723+00	1	t	\N	f	f
1819	PROJECT	Project	test	247931	2022-09-20 08:39:09.340644+00	2022-09-20 08:39:09.340672+00	1	t	\N	f	f
1388	PROJECT	Project	Mitchell & assoc	247500	2022-09-20 08:39:08.422798+00	2022-09-20 08:39:08.422828+00	1	t	\N	f	f
1389	PROJECT	Project	Mitchelle Title -	247501	2022-09-20 08:39:08.422897+00	2022-09-20 08:39:08.422926+00	1	t	\N	f	f
1390	PROJECT	Project	Mitra	247502	2022-09-20 08:39:08.422992+00	2022-09-20 08:39:08.423021+00	1	t	\N	f	f
1391	PROJECT	Project	Molesworth and Repress Liquors Leasing	247503	2022-09-20 08:39:08.423085+00	2022-09-20 08:39:08.423114+00	1	t	\N	f	f
1392	PROJECT	Project	Momphard Painting Sales	247504	2022-09-20 08:39:08.423177+00	2022-09-20 08:39:08.423206+00	1	t	\N	f	f
1393	PROJECT	Project	Monica Parker	247505	2022-09-20 08:39:08.423596+00	2022-09-20 08:39:08.423702+00	1	t	\N	f	f
1394	PROJECT	Project	Moores Builders Agency	247506	2022-09-20 08:39:08.42384+00	2022-09-20 08:39:08.423891+00	1	t	\N	f	f
1395	PROJECT	Project	Moots Painting Distributors	247507	2022-09-20 08:39:08.424169+00	2022-09-20 08:39:08.424214+00	1	t	\N	f	f
1396	PROJECT	Project	Moreb Plumbing Corporation	247508	2022-09-20 08:39:08.424303+00	2022-09-20 08:39:08.42435+00	1	t	\N	f	f
1397	PROJECT	Project	Mortgage Center	247509	2022-09-20 08:39:08.424617+00	2022-09-20 08:39:08.42466+00	1	t	\N	f	f
1398	PROJECT	Project	Moss Builders	247510	2022-09-20 08:39:08.424748+00	2022-09-20 08:39:08.424779+00	1	t	\N	f	f
1399	PROJECT	Project	Mount Lake Terrace Markets Fabricators	247511	2022-09-20 08:39:08.424855+00	2022-09-20 08:39:08.424906+00	1	t	\N	f	f
1400	PROJECT	Project	Moving Store	247512	2022-09-20 08:39:08.425064+00	2022-09-20 08:39:08.425118+00	1	t	\N	f	f
1401	PROJECT	Project	MuscleTech	247513	2022-09-20 08:39:08.425238+00	2022-09-20 08:39:08.425287+00	1	t	\N	f	f
1402	PROJECT	Project	Nania Painting Networking	247514	2022-09-20 08:39:08.425791+00	2022-09-20 08:39:08.425883+00	1	t	\N	f	f
1403	PROJECT	Project	Neal Ferguson	247515	2022-09-20 08:39:08.426045+00	2022-09-20 08:39:08.426221+00	1	t	\N	f	f
1404	PROJECT	Project	Nephew Publishing Group	247516	2022-09-20 08:39:08.426643+00	2022-09-20 08:39:08.426711+00	1	t	\N	f	f
1405	PROJECT	Project	NetPace Promotions	247517	2022-09-20 08:39:08.426869+00	2022-09-20 08:39:08.426934+00	1	t	\N	f	f
1406	PROJECT	Project	NetStar Inc	247518	2022-09-20 08:39:08.427233+00	2022-09-20 08:39:08.427293+00	1	t	\N	f	f
1407	PROJECT	Project	NetSuite Incorp	247519	2022-09-20 08:39:08.427713+00	2022-09-20 08:39:08.427888+00	1	t	\N	f	f
1408	PROJECT	Project	New Design of Rack	247520	2022-09-20 08:39:08.428004+00	2022-09-20 08:39:08.428038+00	1	t	\N	f	f
1409	PROJECT	Project	New Server Rack Design	247521	2022-09-20 08:39:08.428112+00	2022-09-20 08:39:08.428143+00	1	t	\N	f	f
1410	PROJECT	Project	New Ventures	247522	2022-09-20 08:39:08.428211+00	2022-09-20 08:39:08.428242+00	1	t	\N	f	f
1411	PROJECT	Project	Niedzwiedz Antiques and Associates	247523	2022-09-20 08:39:08.428308+00	2022-09-20 08:39:08.428339+00	1	t	\N	f	f
1412	PROJECT	Project	Nikon	247524	2022-09-20 08:39:08.428587+00	2022-09-20 08:39:08.428655+00	1	t	\N	f	f
1413	PROJECT	Project	Nordon Metal Fabricators Systems	247525	2022-09-20 08:39:08.428882+00	2022-09-20 08:39:08.428929+00	1	t	\N	f	f
1414	PROJECT	Project	Novida and Chochrek Leasing Manufacturing	247526	2022-09-20 08:39:08.429017+00	2022-09-20 08:39:08.429048+00	1	t	\N	f	f
1415	PROJECT	Project	Novx	247527	2022-09-20 08:39:08.429113+00	2022-09-20 08:39:08.429142+00	1	t	\N	f	f
1416	PROJECT	Project	ONLINE1	247528	2022-09-20 08:39:08.429207+00	2022-09-20 08:39:08.429481+00	1	t	\N	f	f
1417	PROJECT	Project	OREA	247529	2022-09-20 08:39:08.429561+00	2022-09-20 08:39:08.42959+00	1	t	\N	f	f
1418	PROJECT	Project	OSPE Inc	247530	2022-09-20 08:39:08.429656+00	2022-09-20 08:39:08.429685+00	1	t	\N	f	f
1419	PROJECT	Project	Oaks and Winters Inc	247531	2022-09-20 08:39:08.429758+00	2022-09-20 08:39:08.429786+00	1	t	\N	f	f
1420	PROJECT	Project	Oceanside Hardware	247532	2022-09-20 08:39:08.429845+00	2022-09-20 08:39:08.429873+00	1	t	\N	f	f
1421	PROJECT	Project	Oconner _ Holding Corp.	247533	2022-09-20 08:39:08.429931+00	2022-09-20 08:39:08.429958+00	1	t	\N	f	f
1422	PROJECT	Project	Oeder Liquors Company	247534	2022-09-20 08:39:08.430177+00	2022-09-20 08:39:08.430345+00	1	t	\N	f	f
1494	PROJECT	Project	Randy James	247606	2022-09-20 08:39:08.957653+00	2022-09-20 08:39:08.957764+00	1	t	\N	f	f
1423	PROJECT	Project	Oestreich Liquors Inc.	247535	2022-09-20 08:39:08.430912+00	2022-09-20 08:39:08.430951+00	1	t	\N	f	f
1424	PROJECT	Project	Office Remodel	247536	2022-09-20 08:39:08.431023+00	2022-09-20 08:39:08.431052+00	1	t	\N	f	f
1425	PROJECT	Project	Oiler Corporation	247537	2022-09-20 08:39:08.431111+00	2022-09-20 08:39:08.431138+00	1	t	\N	f	f
1426	PROJECT	Project	Oldsmar Liquors and Associates	247538	2022-09-20 08:39:08.431196+00	2022-09-20 08:39:08.431223+00	1	t	\N	f	f
1427	PROJECT	Project	Oliver Skin Supplies	247539	2022-09-20 08:39:08.43128+00	2022-09-20 08:39:08.431307+00	1	t	\N	f	f
1428	PROJECT	Project	Olympia Antiques Management	247540	2022-09-20 08:39:08.431497+00	2022-09-20 08:39:08.431536+00	1	t	\N	f	f
1429	PROJECT	Project	Orange Leasing -	247541	2022-09-20 08:39:08.431594+00	2022-09-20 08:39:08.431621+00	1	t	\N	f	f
1430	PROJECT	Project	Orion Hardware	247542	2022-09-20 08:39:08.431678+00	2022-09-20 08:39:08.431705+00	1	t	\N	f	f
1431	PROJECT	Project	Orlando Automotive Leasing	247543	2022-09-20 08:39:08.431764+00	2022-09-20 08:39:08.431791+00	1	t	\N	f	f
1432	PROJECT	Project	Ornelas and Ciejka Painting and Associates	247544	2022-09-20 08:39:08.431848+00	2022-09-20 08:39:08.431875+00	1	t	\N	f	f
1433	PROJECT	Project	Ortego Construction Distributors	247545	2022-09-20 08:39:08.431932+00	2022-09-20 08:39:08.431959+00	1	t	\N	f	f
1434	PROJECT	Project	Osler Antiques -	247546	2022-09-20 08:39:08.842721+00	2022-09-20 08:39:08.842772+00	1	t	\N	f	f
1435	PROJECT	Project	Ostling Metal Fabricators Fabricators	247547	2022-09-20 08:39:08.842848+00	2022-09-20 08:39:08.842889+00	1	t	\N	f	f
1436	PROJECT	Project	Ostrzyeki Markets Distributors	247548	2022-09-20 08:39:08.842953+00	2022-09-20 08:39:08.842981+00	1	t	\N	f	f
1437	PROJECT	Project	Owasso Attorneys Holding Corp.	247549	2022-09-20 08:39:08.843039+00	2022-09-20 08:39:08.843076+00	1	t	\N	f	f
1438	PROJECT	Project	Pacific Northwest	247550	2022-09-20 08:39:08.843143+00	2022-09-20 08:39:08.843154+00	1	t	\N	f	f
1439	PROJECT	Project	Pagliari Builders Services	247551	2022-09-20 08:39:08.84335+00	2022-09-20 08:39:08.843378+00	1	t	\N	f	f
1440	PROJECT	Project	Palmer and Barnar Liquors Leasing	247552	2022-09-20 08:39:08.843455+00	2022-09-20 08:39:08.843488+00	1	t	\N	f	f
1441	PROJECT	Project	Palmisano Hospital Fabricators	247553	2022-09-20 08:39:08.843543+00	2022-09-20 08:39:08.843568+00	1	t	\N	f	f
1442	PROJECT	Project	Palys Attorneys	247554	2022-09-20 08:39:08.843622+00	2022-09-20 08:39:08.843659+00	1	t	\N	f	f
1443	PROJECT	Project	Panora Lumber Dynamics	247555	2022-09-20 08:39:08.843729+00	2022-09-20 08:39:08.843752+00	1	t	\N	f	f
1444	PROJECT	Project	Parking Lot Construction	247556	2022-09-20 08:39:08.843808+00	2022-09-20 08:39:08.843821+00	1	t	\N	f	f
1445	PROJECT	Project	Pasanen Attorneys Agency	247557	2022-09-20 08:39:08.843875+00	2022-09-20 08:39:08.843899+00	1	t	\N	f	f
1446	PROJECT	Project	Patel Cafe	247558	2022-09-20 08:39:08.843969+00	2022-09-20 08:39:08.843992+00	1	t	\N	f	f
1447	PROJECT	Project	Paveglio Leasing Leasing	247559	2022-09-20 08:39:08.844052+00	2022-09-20 08:39:08.844066+00	1	t	\N	f	f
1448	PROJECT	Project	Peak Products	247560	2022-09-20 08:39:08.84412+00	2022-09-20 08:39:08.844154+00	1	t	\N	f	f
1449	PROJECT	Project	Penalver Automotive and Associates	247561	2022-09-20 08:39:08.844321+00	2022-09-20 08:39:08.844343+00	1	t	\N	f	f
1450	PROJECT	Project	Penco Medical Inc.	247562	2022-09-20 08:39:08.844396+00	2022-09-20 08:39:08.844433+00	1	t	\N	f	f
1451	PROJECT	Project	Penister Hospital Fabricators	247563	2022-09-20 08:39:08.844506+00	2022-09-20 08:39:08.844557+00	1	t	\N	f	f
1452	PROJECT	Project	Pertuit Liquors Management	247564	2022-09-20 08:39:08.844619+00	2022-09-20 08:39:08.844645+00	1	t	\N	f	f
1453	PROJECT	Project	Peterson Builders & Assoc	247565	2022-09-20 08:39:08.844699+00	2022-09-20 08:39:08.844723+00	1	t	\N	f	f
1454	PROJECT	Project	Petticrew Apartments Incorporated	247566	2022-09-20 08:39:08.844795+00	2022-09-20 08:39:08.844818+00	1	t	\N	f	f
1455	PROJECT	Project	Peveler and Tyrer Software Networking	247567	2022-09-20 08:39:08.844871+00	2022-09-20 08:39:08.844893+00	1	t	\N	f	f
1456	PROJECT	Project	Phillip Van Hook	247568	2022-09-20 08:39:08.844954+00	2022-09-20 08:39:08.844994+00	1	t	\N	f	f
1457	PROJECT	Project	Pickler Construction Leasing	247569	2022-09-20 08:39:08.845192+00	2022-09-20 08:39:08.845501+00	1	t	\N	f	f
1458	PROJECT	Project	Pigler Plumbing Management	247570	2022-09-20 08:39:08.845597+00	2022-09-20 08:39:08.845638+00	1	t	\N	f	f
1459	PROJECT	Project	Pilkerton Windows Sales	247571	2022-09-20 08:39:08.845732+00	2022-09-20 08:39:08.845763+00	1	t	\N	f	f
1460	PROJECT	Project	Pitney Bowes	247572	2022-09-20 08:39:08.845869+00	2022-09-20 08:39:08.845893+00	1	t	\N	f	f
1461	PROJECT	Project	Pittaway Inc	247573	2022-09-20 08:39:08.845944+00	2022-09-20 08:39:08.845964+00	1	t	\N	f	f
1462	PROJECT	Project	Pittsburgh Quantum Analytics	247574	2022-09-20 08:39:08.846016+00	2022-09-20 08:39:08.846037+00	1	t	\N	f	f
1463	PROJECT	Project	Pittsburgh Windows Incorporated	247575	2022-09-20 08:39:08.84611+00	2022-09-20 08:39:08.846139+00	1	t	\N	f	f
1464	PROJECT	Project	Plantronics (EUR)	247576	2022-09-20 08:39:08.846254+00	2022-09-20 08:39:08.846294+00	1	t	\N	f	f
1465	PROJECT	Project	Plexfase Construction Inc.	247577	2022-09-20 08:39:08.846358+00	2022-09-20 08:39:08.846387+00	1	t	\N	f	f
1466	PROJECT	Project	Podvin Software Networking	247578	2022-09-20 08:39:08.846448+00	2022-09-20 08:39:08.846478+00	1	t	\N	f	f
1467	PROJECT	Project	Poland and Burrus Plumbing	247579	2022-09-20 08:39:08.84653+00	2022-09-20 08:39:08.846559+00	1	t	\N	f	f
1468	PROJECT	Project	Polard Windows	247580	2022-09-20 08:39:08.84662+00	2022-09-20 08:39:08.846649+00	1	t	\N	f	f
1469	PROJECT	Project	Pomona Hardware Leasing	247581	2022-09-20 08:39:08.84671+00	2022-09-20 08:39:08.846792+00	1	t	\N	f	f
1470	PROJECT	Project	Ponniah	247582	2022-09-20 08:39:08.846937+00	2022-09-20 08:39:08.846963+00	1	t	\N	f	f
1471	PROJECT	Project	Port Angeles Telecom Networking	247583	2022-09-20 08:39:08.847027+00	2022-09-20 08:39:08.847051+00	1	t	\N	f	f
1472	PROJECT	Project	Port Townsend Title Corporation	247584	2022-09-20 08:39:08.847634+00	2022-09-20 08:39:08.847667+00	1	t	\N	f	f
1473	PROJECT	Project	Pote Leasing Rentals	247585	2022-09-20 08:39:08.84773+00	2022-09-20 08:39:08.847752+00	1	t	\N	f	f
1474	PROJECT	Project	Primas Consulting	247586	2022-09-20 08:39:08.847814+00	2022-09-20 08:39:08.847835+00	1	t	\N	f	f
1475	PROJECT	Project	Princeton Automotive Management	247587	2022-09-20 08:39:08.847888+00	2022-09-20 08:39:08.847917+00	1	t	\N	f	f
1476	PROJECT	Project	Pritts Construction Distributors	247588	2022-09-20 08:39:08.847978+00	2022-09-20 08:39:08.848007+00	1	t	\N	f	f
1477	PROJECT	Project	Progress Inc	247589	2022-09-20 08:39:08.848062+00	2022-09-20 08:39:08.848084+00	1	t	\N	f	f
1478	PROJECT	Project	Prokup Plumbing Corporation	247590	2022-09-20 08:39:08.848145+00	2022-09-20 08:39:08.848174+00	1	t	\N	f	f
1479	PROJECT	Project	Prudential	247591	2022-09-20 08:39:08.84836+00	2022-09-20 08:39:08.84839+00	1	t	\N	f	f
1480	PROJECT	Project	Ptomey Title Group	247592	2022-09-20 08:39:08.848453+00	2022-09-20 08:39:08.848475+00	1	t	\N	f	f
1481	PROJECT	Project	Pueblo Construction Fabricators	247593	2022-09-20 08:39:08.848536+00	2022-09-20 08:39:08.848557+00	1	t	\N	f	f
1482	PROJECT	Project	Pulse	247594	2022-09-20 08:39:08.848608+00	2022-09-20 08:39:08.848637+00	1	t	\N	f	f
1483	PROJECT	Project	Purchase Construction Agency	247595	2022-09-20 08:39:08.848688+00	2022-09-20 08:39:08.848706+00	1	t	\N	f	f
1484	PROJECT	Project	Puyallup Liquors Networking	247596	2022-09-20 08:39:08.955018+00	2022-09-20 08:39:08.955327+00	1	t	\N	f	f
1485	PROJECT	Project	QJunction Inc	247597	2022-09-20 08:39:08.955665+00	2022-09-20 08:39:08.95572+00	1	t	\N	f	f
1486	PROJECT	Project	Qualle Metal Fabricators Distributors	247598	2022-09-20 08:39:08.956141+00	2022-09-20 08:39:08.95633+00	1	t	\N	f	f
1487	PROJECT	Project	Quantum X	247599	2022-09-20 08:39:08.956485+00	2022-09-20 08:39:08.956537+00	1	t	\N	f	f
1488	PROJECT	Project	Quezad Lumber Leasing	247600	2022-09-20 08:39:08.956656+00	2022-09-20 08:39:08.956697+00	1	t	\N	f	f
1489	PROJECT	Project	Quiterio Windows Co.	247601	2022-09-20 08:39:08.956916+00	2022-09-20 08:39:08.956963+00	1	t	\N	f	f
1490	PROJECT	Project	Rabeck Liquors Group	247602	2022-09-20 08:39:08.957081+00	2022-09-20 08:39:08.957125+00	1	t	\N	f	f
1491	PROJECT	Project	Ralphs Attorneys Group	247603	2022-09-20 08:39:08.957198+00	2022-09-20 08:39:08.957228+00	1	t	\N	f	f
1492	PROJECT	Project	Ramal Builders Incorporated	247604	2022-09-20 08:39:08.957289+00	2022-09-20 08:39:08.957301+00	1	t	\N	f	f
1493	PROJECT	Project	Ramsy Publishing Company	247605	2022-09-20 08:39:08.957448+00	2022-09-20 08:39:08.957512+00	1	t	\N	f	f
1495	PROJECT	Project	Randy Rudd	247607	2022-09-20 08:39:08.958152+00	2022-09-20 08:39:08.958327+00	1	t	\N	f	f
1496	PROJECT	Project	Ras Windows -	247608	2022-09-20 08:39:08.959693+00	2022-09-20 08:39:08.959921+00	1	t	\N	f	f
1497	PROJECT	Project	Rastorfer Automotive Holding Corp.	247609	2022-09-20 08:39:08.960099+00	2022-09-20 08:39:08.960144+00	1	t	\N	f	f
1498	PROJECT	Project	Rauf Catering	247610	2022-09-20 08:39:08.960343+00	2022-09-20 08:39:08.960363+00	1	t	\N	f	f
1499	PROJECT	Project	RedPath Sugars	247611	2022-09-20 08:39:08.960428+00	2022-09-20 08:39:08.96045+00	1	t	\N	f	f
1500	PROJECT	Project	Redick Antiques Inc.	247612	2022-09-20 08:39:08.960506+00	2022-09-20 08:39:08.960519+00	1	t	\N	f	f
1501	PROJECT	Project	Reedus Telecom Group	247613	2022-09-20 08:39:08.96057+00	2022-09-20 08:39:08.960591+00	1	t	\N	f	f
1502	PROJECT	Project	Refco	247614	2022-09-20 08:39:08.960819+00	2022-09-20 08:39:08.960848+00	1	t	\N	f	f
1503	PROJECT	Project	Reinfeld and Jurczak Hospital Incorporated	247615	2022-09-20 08:39:08.960911+00	2022-09-20 08:39:08.96094+00	1	t	\N	f	f
1504	PROJECT	Project	Reinhardt and Sabori Painting Group	247616	2022-09-20 08:39:08.961002+00	2022-09-20 08:39:08.961031+00	1	t	\N	f	f
1505	PROJECT	Project	Reisdorf Title Services	247617	2022-09-20 08:39:08.961151+00	2022-09-20 08:39:08.961192+00	1	t	\N	f	f
1506	PROJECT	Project	Reisman Windows Management	247618	2022-09-20 08:39:08.961415+00	2022-09-20 08:39:08.961458+00	1	t	\N	f	f
1507	PROJECT	Project	Remodel	247619	2022-09-20 08:39:08.961526+00	2022-09-20 08:39:08.961548+00	1	t	\N	f	f
1508	PROJECT	Project	Rennemeyer Liquors Systems	247620	2022-09-20 08:39:08.961614+00	2022-09-20 08:39:08.961639+00	1	t	\N	f	f
1509	PROJECT	Project	Republic Builders and Associates	247621	2022-09-20 08:39:08.961702+00	2022-09-20 08:39:08.961792+00	1	t	\N	f	f
1510	PROJECT	Project	Rey Software Inc.	247622	2022-09-20 08:39:08.97052+00	2022-09-20 08:39:08.97058+00	1	t	\N	f	f
1511	PROJECT	Project	Rezentes Catering Dynamics	247623	2022-09-20 08:39:08.970701+00	2022-09-20 08:39:08.97072+00	1	t	\N	f	f
1512	PROJECT	Project	Rhody Leasing and Associates	247624	2022-09-20 08:39:08.970775+00	2022-09-20 08:39:08.970807+00	1	t	\N	f	f
1513	PROJECT	Project	Rickers Apartments Company	247625	2022-09-20 08:39:08.970871+00	2022-09-20 08:39:08.970912+00	1	t	\N	f	f
1514	PROJECT	Project	Ridderhoff Painting Services	247626	2022-09-20 08:39:08.970991+00	2022-09-20 08:39:08.971009+00	1	t	\N	f	f
1515	PROJECT	Project	Ridgeway Corporation	247627	2022-09-20 08:39:08.97105+00	2022-09-20 08:39:08.971071+00	1	t	\N	f	f
1516	PROJECT	Project	Riede Title and Associates	247628	2022-09-20 08:39:08.971141+00	2022-09-20 08:39:08.971181+00	1	t	\N	f	f
1517	PROJECT	Project	Rio Rancho Painting Agency	247629	2022-09-20 08:39:08.971426+00	2022-09-20 08:39:08.971458+00	1	t	\N	f	f
1518	PROJECT	Project	Riverside Hospital and Associates	247630	2022-09-20 08:39:08.971531+00	2022-09-20 08:39:08.971571+00	1	t	\N	f	f
1519	PROJECT	Project	Robare Builders Corporation	247631	2022-09-20 08:39:08.971641+00	2022-09-20 08:39:08.97167+00	1	t	\N	f	f
1520	PROJECT	Project	Robert Brady	247632	2022-09-20 08:39:08.971735+00	2022-09-20 08:39:08.971757+00	1	t	\N	f	f
1521	PROJECT	Project	Robert Huffman	247633	2022-09-20 08:39:08.971837+00	2022-09-20 08:39:08.971883+00	1	t	\N	f	f
1522	PROJECT	Project	Robert Lee	247634	2022-09-20 08:39:08.971937+00	2022-09-20 08:39:08.971956+00	1	t	\N	f	f
1523	PROJECT	Project	Robert Solan	247635	2022-09-20 08:39:08.97201+00	2022-09-20 08:39:08.972029+00	1	t	\N	f	f
1524	PROJECT	Project	Rogers Communication	247636	2022-09-20 08:39:08.972099+00	2022-09-20 08:39:08.972129+00	1	t	\N	f	f
1525	PROJECT	Project	Rosner and Savo Antiques Systems	247637	2022-09-20 08:39:08.972297+00	2022-09-20 08:39:08.972323+00	1	t	\N	f	f
1526	PROJECT	Project	Ross Nepean	247638	2022-09-20 08:39:08.972404+00	2022-09-20 08:39:08.972448+00	1	t	\N	f	f
1527	PROJECT	Project	Roswell Leasing Management	247639	2022-09-20 08:39:08.972504+00	2022-09-20 08:39:08.972525+00	1	t	\N	f	f
1528	PROJECT	Project	Roule and Mattsey _ Management	247640	2022-09-20 08:39:08.972594+00	2022-09-20 08:39:08.972634+00	1	t	\N	f	f
1529	PROJECT	Project	Roundtree Attorneys Inc.	247641	2022-09-20 08:39:08.972704+00	2022-09-20 08:39:08.972737+00	1	t	\N	f	f
1530	PROJECT	Project	Rowie Williams	247642	2022-09-20 08:39:08.972791+00	2022-09-20 08:39:08.97282+00	1	t	\N	f	f
1531	PROJECT	Project	Roycroft Construction	247643	2022-09-20 08:39:08.972891+00	2022-09-20 08:39:08.972913+00	1	t	\N	f	f
1532	PROJECT	Project	Ruleman Title Distributors	247644	2022-09-20 08:39:08.972982+00	2022-09-20 08:39:08.973003+00	1	t	\N	f	f
1533	PROJECT	Project	Russ Mygrant	247645	2022-09-20 08:39:08.973065+00	2022-09-20 08:39:08.973105+00	1	t	\N	f	f
1534	PROJECT	Project	Russell Telecom	247646	2022-09-20 08:39:08.981993+00	2022-09-20 08:39:08.982053+00	1	t	\N	f	f
1535	PROJECT	Project	Ruts Construction Holding Corp.	247647	2022-09-20 08:39:08.982125+00	2022-09-20 08:39:08.982213+00	1	t	\N	f	f
1536	PROJECT	Project	SS&C	247648	2022-09-20 08:39:08.982292+00	2022-09-20 08:39:08.98232+00	1	t	\N	f	f
1537	PROJECT	Project	Saenger _ Inc.	247649	2022-09-20 08:39:08.982537+00	2022-09-20 08:39:08.982599+00	1	t	\N	f	f
1538	PROJECT	Project	Salisbury Attorneys Group	247650	2022-09-20 08:39:08.982673+00	2022-09-20 08:39:08.982714+00	1	t	\N	f	f
1539	PROJECT	Project	Sally Ward	247651	2022-09-20 08:39:08.982943+00	2022-09-20 08:39:08.982989+00	1	t	\N	f	f
1540	PROJECT	Project	Sam Brown	247652	2022-09-20 08:39:08.983102+00	2022-09-20 08:39:08.983131+00	1	t	\N	f	f
1686	PROJECT	Project	Test a	247798	2022-09-20 08:39:09.296831+00	2022-09-20 08:39:09.296991+00	1	t	\N	f	f
1541	PROJECT	Project	Samantha Walker	247653	2022-09-20 08:39:08.98318+00	2022-09-20 08:39:08.983201+00	1	t	\N	f	f
1542	PROJECT	Project	San Angelo Automotive Rentals	247654	2022-09-20 08:39:08.983378+00	2022-09-20 08:39:08.983422+00	1	t	\N	f	f
1543	PROJECT	Project	San Diego Plumbing Distributors	247655	2022-09-20 08:39:08.98349+00	2022-09-20 08:39:08.983519+00	1	t	\N	f	f
1544	PROJECT	Project	San Diego Windows Agency	247656	2022-09-20 08:39:08.983574+00	2022-09-20 08:39:08.983595+00	1	t	\N	f	f
1545	PROJECT	Project	San Francisco Design Center	247657	2022-09-20 08:39:08.983675+00	2022-09-20 08:39:08.98372+00	1	t	\N	f	f
1546	PROJECT	Project	San Luis Obispo Construction Inc.	247658	2022-09-20 08:39:08.98378+00	2022-09-20 08:39:08.983794+00	1	t	\N	f	f
1547	PROJECT	Project	Sandoval Products Inc	247659	2022-09-20 08:39:08.983843+00	2022-09-20 08:39:08.983865+00	1	t	\N	f	f
1548	PROJECT	Project	Sandra Burns	247660	2022-09-20 08:39:08.983917+00	2022-09-20 08:39:08.983956+00	1	t	\N	f	f
1549	PROJECT	Project	Sandwich Antiques Services	247661	2022-09-20 08:39:08.984022+00	2022-09-20 08:39:08.984254+00	1	t	\N	f	f
1550	PROJECT	Project	Sandwich Telecom Sales	247662	2022-09-20 08:39:08.984446+00	2022-09-20 08:39:08.984477+00	1	t	\N	f	f
1551	PROJECT	Project	Sandy King	247663	2022-09-20 08:39:08.984544+00	2022-09-20 08:39:08.984559+00	1	t	\N	f	f
1552	PROJECT	Project	Sandy Whines	247664	2022-09-20 08:39:08.984619+00	2022-09-20 08:39:08.984647+00	1	t	\N	f	f
1553	PROJECT	Project	Santa Ana Telecom Management	247665	2022-09-20 08:39:08.984705+00	2022-09-20 08:39:08.984732+00	1	t	\N	f	f
1554	PROJECT	Project	Santa Fe Springs Construction Corporation	247666	2022-09-20 08:39:08.984789+00	2022-09-20 08:39:08.984816+00	1	t	\N	f	f
1555	PROJECT	Project	Santa Maria Lumber Inc.	247667	2022-09-20 08:39:08.984872+00	2022-09-20 08:39:08.9849+00	1	t	\N	f	f
1556	PROJECT	Project	Santa Monica Attorneys Manufacturing	247668	2022-09-20 08:39:08.984957+00	2022-09-20 08:39:08.984984+00	1	t	\N	f	f
1557	PROJECT	Project	Sarasota Software Rentals	247669	2022-09-20 08:39:08.98504+00	2022-09-20 08:39:08.985068+00	1	t	\N	f	f
1558	PROJECT	Project	Sarchett Antiques Networking	247670	2022-09-20 08:39:08.985124+00	2022-09-20 08:39:08.985151+00	1	t	\N	f	f
1559	PROJECT	Project	Sawatzky Catering Rentals	247671	2022-09-20 08:39:08.985208+00	2022-09-20 08:39:08.985235+00	1	t	\N	f	f
1560	PROJECT	Project	Sax Lumber Co.	247672	2022-09-20 08:39:08.985292+00	2022-09-20 08:39:08.985319+00	1	t	\N	f	f
1561	PROJECT	Project	Scalley Construction Inc.	247673	2022-09-20 08:39:08.985492+00	2022-09-20 08:39:08.985532+00	1	t	\N	f	f
1562	PROJECT	Project	Schlicker Metal Fabricators Fabricators	247674	2022-09-20 08:39:08.98559+00	2022-09-20 08:39:08.985617+00	1	t	\N	f	f
1563	PROJECT	Project	Schmauder Markets Corporation	247675	2022-09-20 08:39:08.985674+00	2022-09-20 08:39:08.985701+00	1	t	\N	f	f
1564	PROJECT	Project	Schmidt Sporting Goods	247676	2022-09-20 08:39:08.985758+00	2022-09-20 08:39:08.985785+00	1	t	\N	f	f
1565	PROJECT	Project	Schneck Automotive Group	247677	2022-09-20 08:39:08.985842+00	2022-09-20 08:39:08.985869+00	1	t	\N	f	f
1566	PROJECT	Project	Scholl Catering -	247678	2022-09-20 08:39:08.985925+00	2022-09-20 08:39:08.985953+00	1	t	\N	f	f
1567	PROJECT	Project	Schreck Hardware Systems	247679	2022-09-20 08:39:08.986009+00	2022-09-20 08:39:08.986036+00	1	t	\N	f	f
1568	PROJECT	Project	Schwarzenbach Attorneys Systems	247680	2022-09-20 08:39:08.986093+00	2022-09-20 08:39:08.98612+00	1	t	\N	f	f
1569	PROJECT	Project	Scottsbluff Lumber -	247681	2022-09-20 08:39:08.986176+00	2022-09-20 08:39:08.986204+00	1	t	\N	f	f
1570	PROJECT	Project	Scottsbluff Plumbing Rentals	247682	2022-09-20 08:39:08.986261+00	2022-09-20 08:39:08.986288+00	1	t	\N	f	f
1571	PROJECT	Project	Scullion Telecom Agency	247683	2022-09-20 08:39:08.986345+00	2022-09-20 08:39:08.986484+00	1	t	\N	f	f
1572	PROJECT	Project	Sebastian Inc.	247684	2022-09-20 08:39:08.986553+00	2022-09-20 08:39:08.986592+00	1	t	\N	f	f
1573	PROJECT	Project	Sebek Builders Distributors	247685	2022-09-20 08:39:08.986649+00	2022-09-20 08:39:08.986676+00	1	t	\N	f	f
1574	PROJECT	Project	Sedlak Inc	247686	2022-09-20 08:39:08.986733+00	2022-09-20 08:39:08.986759+00	1	t	\N	f	f
1575	PROJECT	Project	Seecharan and Horten Hardware Manufacturing	247687	2022-09-20 08:39:08.986816+00	2022-09-20 08:39:08.986843+00	1	t	\N	f	f
1576	PROJECT	Project	Seena Rose	247688	2022-09-20 08:39:08.986899+00	2022-09-20 08:39:08.986926+00	1	t	\N	f	f
1577	PROJECT	Project	Seilhymer Antiques Distributors	247689	2022-09-20 08:39:08.986983+00	2022-09-20 08:39:08.98701+00	1	t	\N	f	f
1578	PROJECT	Project	Selders Distributors	247690	2022-09-20 08:39:08.987066+00	2022-09-20 08:39:08.987093+00	1	t	\N	f	f
1579	PROJECT	Project	Selia Metal Fabricators Company	247691	2022-09-20 08:39:08.987149+00	2022-09-20 08:39:08.987176+00	1	t	\N	f	f
1580	PROJECT	Project	Seney Windows Agency	247692	2022-09-20 08:39:08.987247+00	2022-09-20 08:39:08.988044+00	1	t	\N	f	f
1581	PROJECT	Project	Sequim Automotive Systems	247693	2022-09-20 08:39:08.98817+00	2022-09-20 08:39:08.988326+00	1	t	\N	f	f
1582	PROJECT	Project	Service Job	247694	2022-09-20 08:39:08.988815+00	2022-09-20 08:39:08.98908+00	1	t	\N	f	f
1583	PROJECT	Project	Seyler Title Distributors	247695	2022-09-20 08:39:08.989186+00	2022-09-20 08:39:08.989363+00	1	t	\N	f	f
1584	PROJECT	Project	Shackelton Hospital Sales	247696	2022-09-20 08:39:08.998889+00	2022-09-20 08:39:08.998926+00	1	t	\N	f	f
1586	PROJECT	Project	Sheinbein Construction Fabricators	247698	2022-09-20 08:39:08.999391+00	2022-09-20 08:39:08.999434+00	1	t	\N	f	f
1587	PROJECT	Project	Shininger Lumber Holding Corp.	247699	2022-09-20 08:39:08.999522+00	2022-09-20 08:39:08.999545+00	1	t	\N	f	f
1588	PROJECT	Project	Shutter Title Services	247700	2022-09-20 08:39:08.999598+00	2022-09-20 08:39:08.999627+00	1	t	\N	f	f
1589	PROJECT	Project	Siddiq Software -	247701	2022-09-20 08:39:08.999736+00	2022-09-20 08:39:08.99978+00	1	t	\N	f	f
1590	PROJECT	Project	Simatry	247702	2022-09-20 08:39:08.999894+00	2022-09-20 08:39:08.999931+00	1	t	\N	f	f
1591	PROJECT	Project	Simi Valley Telecom Dynamics	247703	2022-09-20 08:39:09.000042+00	2022-09-20 08:39:09.000081+00	1	t	\N	f	f
1592	PROJECT	Project	Sindt Electric	247704	2022-09-20 08:39:09.000158+00	2022-09-20 08:39:09.000335+00	1	t	\N	f	f
1593	PROJECT	Project	Skibo Construction Dynamics	247705	2022-09-20 08:39:09.000442+00	2022-09-20 08:39:09.000462+00	1	t	\N	f	f
1594	PROJECT	Project	Slankard Automotive	247706	2022-09-20 08:39:09.000514+00	2022-09-20 08:39:09.000543+00	1	t	\N	f	f
1595	PROJECT	Project	Slatter Metal Fabricators Inc.	247707	2022-09-20 08:39:09.000604+00	2022-09-20 08:39:09.000623+00	1	t	\N	f	f
1596	PROJECT	Project	SlingShot Communications	247708	2022-09-20 08:39:09.000676+00	2022-09-20 08:39:09.000705+00	1	t	\N	f	f
1597	PROJECT	Project	Sloman and Zeccardi Builders Agency	247709	2022-09-20 08:39:09.000765+00	2022-09-20 08:39:09.000789+00	1	t	\N	f	f
1598	PROJECT	Project	Smelley _ Manufacturing	247710	2022-09-20 08:39:09.000841+00	2022-09-20 08:39:09.000869+00	1	t	\N	f	f
1599	PROJECT	Project	Smith East	247711	2022-09-20 08:39:09.000921+00	2022-09-20 08:39:09.00095+00	1	t	\N	f	f
1600	PROJECT	Project	Smith Inc.	247712	2022-09-20 08:39:09.001009+00	2022-09-20 08:39:09.00103+00	1	t	\N	f	f
1601	PROJECT	Project	Smith Photographic Equipment	247713	2022-09-20 08:39:09.001091+00	2022-09-20 08:39:09.001116+00	1	t	\N	f	f
1602	PROJECT	Project	Smith West	247714	2022-09-20 08:39:09.001168+00	2022-09-20 08:39:09.001196+00	1	t	\N	f	f
1603	PROJECT	Project	Snode and Draper Leasing Rentals	247715	2022-09-20 08:39:09.001347+00	2022-09-20 08:39:09.001367+00	1	t	\N	f	f
1604	PROJECT	Project	Soares Builders Inc.	247716	2022-09-20 08:39:09.001416+00	2022-09-20 08:39:09.001446+00	1	t	\N	f	f
1605	PROJECT	Project	Solidd Group Ltd	247717	2022-09-20 08:39:09.001499+00	2022-09-20 08:39:09.001517+00	1	t	\N	f	f
1606	PROJECT	Project	Soltrus	247718	2022-09-20 08:39:09.001559+00	2022-09-20 08:39:09.001579+00	1	t	\N	f	f
1607	PROJECT	Project	Solymani Electric Leasing	247719	2022-09-20 08:39:09.00164+00	2022-09-20 08:39:09.001661+00	1	t	\N	f	f
1608	PROJECT	Project	Sossong Plumbing Holding Corp.	247720	2022-09-20 08:39:09.001713+00	2022-09-20 08:39:09.001742+00	1	t	\N	f	f
1609	PROJECT	Project	South East	247721	2022-09-20 08:39:09.001803+00	2022-09-20 08:39:09.001832+00	1	t	\N	f	f
1610	PROJECT	Project	Spany ltd	247722	2022-09-20 08:39:09.001892+00	2022-09-20 08:39:09.001915+00	1	t	\N	f	f
1611	PROJECT	Project	Spectrum Eye	247723	2022-09-20 08:39:09.001968+00	2022-09-20 08:39:09.001997+00	1	t	\N	f	f
1612	PROJECT	Project	Sport Station	247724	2022-09-20 08:39:09.002057+00	2022-09-20 08:39:09.002086+00	1	t	\N	f	f
1613	PROJECT	Project	Sports Authority	247725	2022-09-20 08:39:09.00214+00	2022-09-20 08:39:09.002151+00	1	t	\N	f	f
1614	PROJECT	Project	Spurgin Telecom Agency	247726	2022-09-20 08:39:09.002479+00	2022-09-20 08:39:09.002503+00	1	t	\N	f	f
1615	PROJECT	Project	St Lawrence Starch	247727	2022-09-20 08:39:09.002551+00	2022-09-20 08:39:09.002564+00	1	t	\N	f	f
1616	PROJECT	Project	St. Francis Yacht Club	247728	2022-09-20 08:39:09.002614+00	2022-09-20 08:39:09.002638+00	1	t	\N	f	f
1617	PROJECT	Project	St. Mark's Church	247729	2022-09-20 08:39:09.0027+00	2022-09-20 08:39:09.002729+00	1	t	\N	f	f
1618	PROJECT	Project	Stai Publishing -	247730	2022-09-20 08:39:09.002785+00	2022-09-20 08:39:09.002812+00	1	t	\N	f	f
1619	PROJECT	Project	Stampe Leasing and Associates	247731	2022-09-20 08:39:09.002869+00	2022-09-20 08:39:09.002896+00	1	t	\N	f	f
1620	PROJECT	Project	Stantec Inc	247732	2022-09-20 08:39:09.002954+00	2022-09-20 08:39:09.002981+00	1	t	\N	f	f
1621	PROJECT	Project	Star Structural	247733	2022-09-20 08:39:09.003038+00	2022-09-20 08:39:09.003065+00	1	t	\N	f	f
1622	PROJECT	Project	Steacy Tech Inc	247734	2022-09-20 08:39:09.003122+00	2022-09-20 08:39:09.003149+00	1	t	\N	f	f
1623	PROJECT	Project	Steep and Cloud Liquors Co.	247735	2022-09-20 08:39:09.003207+00	2022-09-20 08:39:09.003234+00	1	t	\N	f	f
1624	PROJECT	Project	Steffensmeier Markets Co.	247736	2022-09-20 08:39:09.003291+00	2022-09-20 08:39:09.003319+00	1	t	\N	f	f
1625	PROJECT	Project	Steinberg Electric Networking	247737	2022-09-20 08:39:09.003469+00	2022-09-20 08:39:09.003508+00	1	t	\N	f	f
1626	PROJECT	Project	Stella Sebastian Inc	247738	2022-09-20 08:39:09.003565+00	2022-09-20 08:39:09.003592+00	1	t	\N	f	f
1627	PROJECT	Project	Stephan Simms	247739	2022-09-20 08:39:09.003649+00	2022-09-20 08:39:09.003676+00	1	t	\N	f	f
1628	PROJECT	Project	Sternberger Telecom Incorporated	247740	2022-09-20 08:39:09.003733+00	2022-09-20 08:39:09.00376+00	1	t	\N	f	f
1629	PROJECT	Project	Sterr Lumber Systems	247741	2022-09-20 08:39:09.0041+00	2022-09-20 08:39:09.004132+00	1	t	\N	f	f
1630	PROJECT	Project	Steve Davis	247742	2022-09-20 08:39:09.004191+00	2022-09-20 08:39:09.004212+00	1	t	\N	f	f
1631	PROJECT	Project	Steve Smith	247743	2022-09-20 08:39:09.004378+00	2022-09-20 08:39:09.004409+00	1	t	\N	f	f
1632	PROJECT	Project	Stewart's Valet Parking	247744	2022-09-20 08:39:09.00451+00	2022-09-20 08:39:09.00454+00	1	t	\N	f	f
1633	PROJECT	Project	Stirling Truck Services	247745	2022-09-20 08:39:09.00468+00	2022-09-20 08:39:09.004726+00	1	t	\N	f	f
1634	PROJECT	Project	Stitch Software Distributors	247746	2022-09-20 08:39:09.279987+00	2022-09-20 08:39:09.280029+00	1	t	\N	f	f
1635	PROJECT	Project	Stoett Telecom Rentals	247747	2022-09-20 08:39:09.280094+00	2022-09-20 08:39:09.280123+00	1	t	\N	f	f
1636	PROJECT	Project	Stofflet Hardware Incorporated	247748	2022-09-20 08:39:09.280185+00	2022-09-20 08:39:09.280214+00	1	t	\N	f	f
1637	PROJECT	Project	Stone & Cox	247749	2022-09-20 08:39:09.280275+00	2022-09-20 08:39:09.280304+00	1	t	\N	f	f
1638	PROJECT	Project	Stonum Catering Group	247750	2022-09-20 08:39:09.280453+00	2022-09-20 08:39:09.280483+00	1	t	\N	f	f
1639	PROJECT	Project	Storch Title Manufacturing	247751	2022-09-20 08:39:09.280545+00	2022-09-20 08:39:09.280574+00	1	t	\N	f	f
1640	PROJECT	Project	Stotelmyer and Conelly Metal Fabricators Group	247752	2022-09-20 08:39:09.280634+00	2022-09-20 08:39:09.280664+00	1	t	\N	f	f
1641	PROJECT	Project	Stower Electric Company	247753	2022-09-20 08:39:09.280725+00	2022-09-20 08:39:09.280754+00	1	t	\N	f	f
1642	PROJECT	Project	Streib and Cravy Hardware Rentals	247754	2022-09-20 08:39:09.280814+00	2022-09-20 08:39:09.280844+00	1	t	\N	f	f
1643	PROJECT	Project	Sturrup Antiques Management	247755	2022-09-20 08:39:09.280904+00	2022-09-20 08:39:09.280934+00	1	t	\N	f	f
1644	PROJECT	Project	Summerton Hospital Services	247756	2022-09-20 08:39:09.280995+00	2022-09-20 08:39:09.281024+00	1	t	\N	f	f
1645	PROJECT	Project	Summons Apartments Company	247757	2022-09-20 08:39:09.281085+00	2022-09-20 08:39:09.281114+00	1	t	\N	f	f
1646	PROJECT	Project	Sumter Apartments Systems	247758	2022-09-20 08:39:09.281174+00	2022-09-20 08:39:09.281203+00	1	t	\N	f	f
1647	PROJECT	Project	Sunnybrook Hospital	247759	2022-09-20 08:39:09.281264+00	2022-09-20 08:39:09.281293+00	1	t	\N	f	f
1648	PROJECT	Project	Superior Car care Inc.	247760	2022-09-20 08:39:09.281353+00	2022-09-20 08:39:09.281464+00	1	t	\N	f	f
1649	PROJECT	Project	Support T&M	247761	2022-09-20 08:39:09.281526+00	2022-09-20 08:39:09.281556+00	1	t	\N	f	f
1650	PROJECT	Project	Sur Windows Services	247762	2022-09-20 08:39:09.281616+00	2022-09-20 08:39:09.281645+00	1	t	\N	f	f
1651	PROJECT	Project	Svancara Antiques Holding Corp.	247763	2022-09-20 08:39:09.281706+00	2022-09-20 08:39:09.281735+00	1	t	\N	f	f
1652	PROJECT	Project	Swanger Spirits	247764	2022-09-20 08:39:09.281795+00	2022-09-20 08:39:09.281825+00	1	t	\N	f	f
1653	PROJECT	Project	Sweeton and Ketron Liquors Group	247765	2022-09-20 08:39:09.281885+00	2022-09-20 08:39:09.281914+00	1	t	\N	f	f
1654	PROJECT	Project	Swiech Telecom Networking	247766	2022-09-20 08:39:09.281974+00	2022-09-20 08:39:09.282003+00	1	t	\N	f	f
1655	PROJECT	Project	Swinea Antiques Holding Corp.	247767	2022-09-20 08:39:09.282063+00	2022-09-20 08:39:09.282093+00	1	t	\N	f	f
1656	PROJECT	Project	Symore Construction Dynamics	247768	2022-09-20 08:39:09.282153+00	2022-09-20 08:39:09.282182+00	1	t	\N	f	f
1657	PROJECT	Project	Szewczyk Apartments Holding Corp.	247769	2022-09-20 08:39:09.282242+00	2022-09-20 08:39:09.282271+00	1	t	\N	f	f
1658	PROJECT	Project	T-M Manufacturing Corp.	247770	2022-09-20 08:39:09.282331+00	2022-09-20 08:39:09.282445+00	1	t	\N	f	f
1659	PROJECT	Project	TAB Ltd	247771	2022-09-20 08:39:09.282508+00	2022-09-20 08:39:09.282538+00	1	t	\N	f	f
1660	PROJECT	Project	TES Inc	247772	2022-09-20 08:39:09.282599+00	2022-09-20 08:39:09.282628+00	1	t	\N	f	f
1662	PROJECT	Project	TST Solutions Inc	247774	2022-09-20 08:39:09.282778+00	2022-09-20 08:39:09.282807+00	1	t	\N	f	f
1663	PROJECT	Project	TTS inc	247775	2022-09-20 08:39:09.282867+00	2022-09-20 08:39:09.282897+00	1	t	\N	f	f
1664	PROJECT	Project	TWC Financial	247776	2022-09-20 08:39:09.282956+00	2022-09-20 08:39:09.282985+00	1	t	\N	f	f
1665	PROJECT	Project	Taback Construction Leasing	247777	2022-09-20 08:39:09.283046+00	2022-09-20 08:39:09.283075+00	1	t	\N	f	f
1666	PROJECT	Project	Talboti and Pauli Title Agency	247778	2022-09-20 08:39:09.283136+00	2022-09-20 08:39:09.283165+00	1	t	\N	f	f
1667	PROJECT	Project	Tam Liquors	247779	2022-09-20 08:39:09.283225+00	2022-09-20 08:39:09.283254+00	1	t	\N	f	f
1668	PROJECT	Project	Tamara Gibson	247780	2022-09-20 08:39:09.283314+00	2022-09-20 08:39:09.283344+00	1	t	\N	f	f
1669	PROJECT	Project	Tanya Guerrero	247781	2022-09-20 08:39:09.283488+00	2022-09-20 08:39:09.283518+00	1	t	\N	f	f
1670	PROJECT	Project	Tarangelo and Mccrea Apartments Holding Corp.	247782	2022-09-20 08:39:09.28358+00	2022-09-20 08:39:09.283609+00	1	t	\N	f	f
1671	PROJECT	Project	Tarbutton Software Management	247783	2022-09-20 08:39:09.28367+00	2022-09-20 08:39:09.283699+00	1	t	\N	f	f
1672	PROJECT	Project	TargetVision	247784	2022-09-20 08:39:09.283758+00	2022-09-20 08:39:09.283792+00	1	t	\N	f	f
1673	PROJECT	Project	Taverna Liquors Networking	247785	2022-09-20 08:39:09.283854+00	2022-09-20 08:39:09.283883+00	1	t	\N	f	f
1674	PROJECT	Project	Team Industrial	247786	2022-09-20 08:39:09.283944+00	2022-09-20 08:39:09.283974+00	1	t	\N	f	f
1675	PROJECT	Project	Tebo Builders Management	247787	2022-09-20 08:39:09.284035+00	2022-09-20 08:39:09.284064+00	1	t	\N	f	f
1676	PROJECT	Project	Technology Consultants	247788	2022-09-20 08:39:09.284124+00	2022-09-20 08:39:09.284153+00	1	t	\N	f	f
1677	PROJECT	Project	Teddy Leasing Manufacturing	247789	2022-09-20 08:39:09.284213+00	2022-09-20 08:39:09.284242+00	1	t	\N	f	f
1678	PROJECT	Project	Tenen Markets Dynamics	247790	2022-09-20 08:39:09.284302+00	2022-09-20 08:39:09.284331+00	1	t	\N	f	f
1679	PROJECT	Project	Territory JMP 2	247791	2022-09-20 08:39:09.284475+00	2022-09-20 08:39:09.284505+00	1	t	\N	f	f
1680	PROJECT	Project	Territory JMP 3	247792	2022-09-20 08:39:09.284566+00	2022-09-20 08:39:09.284596+00	1	t	\N	f	f
1681	PROJECT	Project	Territory JMP 4	247793	2022-09-20 08:39:09.284657+00	2022-09-20 08:39:09.284686+00	1	t	\N	f	f
1682	PROJECT	Project	Tessa Darby	247794	2022-09-20 08:39:09.284746+00	2022-09-20 08:39:09.284775+00	1	t	\N	f	f
1683	PROJECT	Project	Test 2	247795	2022-09-20 08:39:09.284836+00	2022-09-20 08:39:09.284865+00	1	t	\N	f	f
1684	PROJECT	Project	Test 3	247796	2022-09-20 08:39:09.296187+00	2022-09-20 08:39:09.296409+00	1	t	\N	f	f
1685	PROJECT	Project	Test Test	247797	2022-09-20 08:39:09.296609+00	2022-09-20 08:39:09.29664+00	1	t	\N	f	f
1687	PROJECT	Project	Teton Winter Sports	247799	2022-09-20 08:39:09.297157+00	2022-09-20 08:39:09.297187+00	1	t	\N	f	f
1688	PROJECT	Project	The Coffee Corner	247800	2022-09-20 08:39:09.297636+00	2022-09-20 08:39:09.297667+00	1	t	\N	f	f
1689	PROJECT	Project	The Liquor Barn	247801	2022-09-20 08:39:09.297861+00	2022-09-20 08:39:09.297891+00	1	t	\N	f	f
1690	PROJECT	Project	The Validation Group	247802	2022-09-20 08:39:09.29808+00	2022-09-20 08:39:09.298352+00	1	t	\N	f	f
1691	PROJECT	Project	Thermo Electron Corporation	247803	2022-09-20 08:39:09.298422+00	2022-09-20 08:39:09.298718+00	1	t	\N	f	f
1692	PROJECT	Project	Therrell Publishing Networking	247804	2022-09-20 08:39:09.298913+00	2022-09-20 08:39:09.298943+00	1	t	\N	f	f
1693	PROJECT	Project	Thomison Windows Networking	247805	2022-09-20 08:39:09.299135+00	2022-09-20 08:39:09.299247+00	1	t	\N	f	f
1694	PROJECT	Project	Thongchanh Telecom Rentals	247806	2022-09-20 08:39:09.299378+00	2022-09-20 08:39:09.299538+00	1	t	\N	f	f
1695	PROJECT	Project	Thorne & Assoc	247807	2022-09-20 08:39:09.299725+00	2022-09-20 08:39:09.299756+00	1	t	\N	f	f
1697	PROJECT	Project	Timinsky Lumber Dynamics	247809	2022-09-20 08:39:09.300167+00	2022-09-20 08:39:09.300303+00	1	t	\N	f	f
1698	PROJECT	Project	Timmy Brown	247810	2022-09-20 08:39:09.300433+00	2022-09-20 08:39:09.300592+00	1	t	\N	f	f
1699	PROJECT	Project	Titam Business Services	247811	2022-09-20 08:39:09.300829+00	2022-09-20 08:39:09.300859+00	1	t	\N	f	f
1700	PROJECT	Project	Tom Calhoun	247812	2022-09-20 08:39:09.301645+00	2022-09-20 08:39:09.30171+00	1	t	\N	f	f
1701	PROJECT	Project	Tom Kratz	247813	2022-09-20 08:39:09.301806+00	2022-09-20 08:39:09.302179+00	1	t	\N	f	f
1702	PROJECT	Project	Tom MacGillivray	247814	2022-09-20 08:39:09.30244+00	2022-09-20 08:39:09.3026+00	1	t	\N	f	f
1703	PROJECT	Project	Tomlinson	247815	2022-09-20 08:39:09.302812+00	2022-09-20 08:39:09.302839+00	1	t	\N	f	f
1704	PROJECT	Project	Tony Matsuda	247816	2022-09-20 08:39:09.303108+00	2022-09-20 08:39:09.303153+00	1	t	\N	f	f
1705	PROJECT	Project	Top Drawer Creative	247817	2022-09-20 08:39:09.303446+00	2022-09-20 08:39:09.30348+00	1	t	\N	f	f
1706	PROJECT	Project	Touchard Liquors Holding Corp.	247818	2022-09-20 08:39:09.305886+00	2022-09-20 08:39:09.30628+00	1	t	\N	f	f
1707	PROJECT	Project	Tower AV and Telephone Install	247819	2022-09-20 08:39:09.306822+00	2022-09-20 08:39:09.306931+00	1	t	\N	f	f
1708	PROJECT	Project	Tower PL-01	247820	2022-09-20 08:39:09.307197+00	2022-09-20 08:39:09.307238+00	1	t	\N	f	f
1709	PROJECT	Project	Towsend Software Co.	247821	2022-09-20 08:39:09.307892+00	2022-09-20 08:39:09.307947+00	1	t	\N	f	f
1710	PROJECT	Project	Tracy Attorneys Management	247822	2022-09-20 08:39:09.308236+00	2022-09-20 08:39:09.308558+00	1	t	\N	f	f
1711	PROJECT	Project	Travis Gilbert	247823	2022-09-20 08:39:09.3087+00	2022-09-20 08:39:09.308959+00	1	t	\N	f	f
1712	PROJECT	Project	Trebor Allen Candy	247824	2022-09-20 08:39:09.310193+00	2022-09-20 08:39:09.310531+00	1	t	\N	f	f
1713	PROJECT	Project	Tredwell Lumber Holding Corp.	247825	2022-09-20 08:39:09.310733+00	2022-09-20 08:39:09.310802+00	1	t	\N	f	f
1714	PROJECT	Project	Trent Barry	247826	2022-09-20 08:39:09.310981+00	2022-09-20 08:39:09.311066+00	1	t	\N	f	f
1715	PROJECT	Project	Trenton Upwood Ltd	247827	2022-09-20 08:39:09.3118+00	2022-09-20 08:39:09.311859+00	1	t	\N	f	f
1716	PROJECT	Project	Tucson Apartments and Associates	247828	2022-09-20 08:39:09.311964+00	2022-09-20 08:39:09.312007+00	1	t	\N	f	f
1717	PROJECT	Project	Turso Catering Agency	247829	2022-09-20 08:39:09.312109+00	2022-09-20 08:39:09.312196+00	1	t	\N	f	f
1718	PROJECT	Project	Tuy and Sinha Construction Manufacturing	247830	2022-09-20 08:39:09.312375+00	2022-09-20 08:39:09.312401+00	1	t	\N	f	f
1719	PROJECT	Project	Twigg Attorneys Company	247831	2022-09-20 08:39:09.312461+00	2022-09-20 08:39:09.312482+00	1	t	\N	f	f
1720	PROJECT	Project	Twine Title Group	247832	2022-09-20 08:39:09.312541+00	2022-09-20 08:39:09.312562+00	1	t	\N	f	f
1721	PROJECT	Project	UK Customer	247833	2022-09-20 08:39:09.312634+00	2022-09-20 08:39:09.31267+00	1	t	\N	f	f
1722	PROJECT	Project	Udoh Publishing Manufacturing	247834	2022-09-20 08:39:09.312727+00	2022-09-20 08:39:09.312749+00	1	t	\N	f	f
1723	PROJECT	Project	Uimari Antiques Agency	247835	2022-09-20 08:39:09.312855+00	2022-09-20 08:39:09.3129+00	1	t	\N	f	f
1724	PROJECT	Project	Umali Publishing Distributors	247836	2022-09-20 08:39:09.313028+00	2022-09-20 08:39:09.313068+00	1	t	\N	f	f
1725	PROJECT	Project	Umbrell Liquors Rentals	247837	2022-09-20 08:39:09.313145+00	2022-09-20 08:39:09.313162+00	1	t	\N	f	f
1726	PROJECT	Project	Umeh Telecom Management	247838	2022-09-20 08:39:09.313339+00	2022-09-20 08:39:09.313377+00	1	t	\N	f	f
1727	PROJECT	Project	Underdown Metal Fabricators and Associates	247839	2022-09-20 08:39:09.313463+00	2022-09-20 08:39:09.313494+00	1	t	\N	f	f
1728	PROJECT	Project	Underwood New York	247840	2022-09-20 08:39:09.313556+00	2022-09-20 08:39:09.313584+00	1	t	\N	f	f
1729	PROJECT	Project	Underwood Systems	247841	2022-09-20 08:39:09.313646+00	2022-09-20 08:39:09.313658+00	1	t	\N	f	f
1730	PROJECT	Project	UniExchange	247842	2022-09-20 08:39:09.31371+00	2022-09-20 08:39:09.313732+00	1	t	\N	f	f
1731	PROJECT	Project	Unnold Hospital Co.	247843	2022-09-20 08:39:09.313812+00	2022-09-20 08:39:09.313854+00	1	t	\N	f	f
1732	PROJECT	Project	Upper 49th	247844	2022-09-20 08:39:09.313918+00	2022-09-20 08:39:09.313931+00	1	t	\N	f	f
1733	PROJECT	Project	Ursery Publishing Group	247845	2022-09-20 08:39:09.313988+00	2022-09-20 08:39:09.31401+00	1	t	\N	f	f
1734	PROJECT	Project	Urwin Leasing Group	247846	2022-09-20 08:39:09.322777+00	2022-09-20 08:39:09.322831+00	1	t	\N	f	f
1735	PROJECT	Project	Valley Center Catering Leasing	247847	2022-09-20 08:39:09.322976+00	2022-09-20 08:39:09.323029+00	1	t	\N	f	f
1736	PROJECT	Project	Vanaken Apartments Holding Corp.	247848	2022-09-20 08:39:09.323123+00	2022-09-20 08:39:09.323174+00	1	t	\N	f	f
1737	PROJECT	Project	Vanasse Antiques Networking	247849	2022-09-20 08:39:09.323415+00	2022-09-20 08:39:09.323459+00	1	t	\N	f	f
1738	PROJECT	Project	Vance Construction and Associates	247850	2022-09-20 08:39:09.32353+00	2022-09-20 08:39:09.323559+00	1	t	\N	f	f
1739	PROJECT	Project	Vanwyngaarden Title Systems	247851	2022-09-20 08:39:09.32362+00	2022-09-20 08:39:09.323659+00	1	t	\N	f	f
1740	PROJECT	Project	Vegas Tours	247852	2022-09-20 08:39:09.323731+00	2022-09-20 08:39:09.323743+00	1	t	\N	f	f
1741	PROJECT	Project	Vellekamp Title Distributors	247853	2022-09-20 08:39:09.323794+00	2022-09-20 08:39:09.323823+00	1	t	\N	f	f
1742	PROJECT	Project	Veradale Telecom Manufacturing	247854	2022-09-20 08:39:09.323884+00	2022-09-20 08:39:09.323913+00	1	t	\N	f	f
1743	PROJECT	Project	Vermont Attorneys Company	247855	2022-09-20 08:39:09.323973+00	2022-09-20 08:39:09.324002+00	1	t	\N	f	f
1744	PROJECT	Project	Verrelli Construction -	247856	2022-09-20 08:39:09.324067+00	2022-09-20 08:39:09.324096+00	1	t	\N	f	f
1745	PROJECT	Project	Vertex	247857	2022-09-20 08:39:09.324156+00	2022-09-20 08:39:09.324194+00	1	t	\N	f	f
1746	PROJECT	Project	Vessel Painting Holding Corp.	247858	2022-09-20 08:39:09.324251+00	2022-09-20 08:39:09.324279+00	1	t	\N	f	f
1747	PROJECT	Project	Villanova Lumber Systems	247859	2022-09-20 08:39:09.324601+00	2022-09-20 08:39:09.324631+00	1	t	\N	f	f
1748	PROJECT	Project	Virginia Beach Hospital Manufacturing	247860	2022-09-20 08:39:09.324689+00	2022-09-20 08:39:09.324716+00	1	t	\N	f	f
1749	PROJECT	Project	Vista Lumber Agency	247861	2022-09-20 08:39:09.324773+00	2022-09-20 08:39:09.3248+00	1	t	\N	f	f
1750	PROJECT	Project	Vivas Electric Sales	247862	2022-09-20 08:39:09.324856+00	2022-09-20 08:39:09.324883+00	1	t	\N	f	f
1751	PROJECT	Project	Vodaphone	247863	2022-09-20 08:39:09.324941+00	2022-09-20 08:39:09.324968+00	1	t	\N	f	f
1752	PROJECT	Project	Volden Publishing Systems	247864	2022-09-20 08:39:09.325133+00	2022-09-20 08:39:09.325216+00	1	t	\N	f	f
1753	PROJECT	Project	Volmar Liquors and Associates	247865	2022-09-20 08:39:09.325446+00	2022-09-20 08:39:09.325488+00	1	t	\N	f	f
1754	PROJECT	Project	Volmink Builders Inc.	247866	2022-09-20 08:39:09.325569+00	2022-09-20 08:39:09.325601+00	1	t	\N	f	f
1755	PROJECT	Project	Wagenheim Painting and Associates	247867	2022-09-20 08:39:09.326388+00	2022-09-20 08:39:09.326452+00	1	t	\N	f	f
1756	PROJECT	Project	Wahlers Lumber Management	247868	2022-09-20 08:39:09.326534+00	2022-09-20 08:39:09.326565+00	1	t	\N	f	f
1757	PROJECT	Project	Wallace Printers	247869	2022-09-20 08:39:09.326642+00	2022-09-20 08:39:09.326684+00	1	t	\N	f	f
1758	PROJECT	Project	Walter Martin	247870	2022-09-20 08:39:09.32677+00	2022-09-20 08:39:09.326803+00	1	t	\N	f	f
1759	PROJECT	Project	Walters Production Company	247871	2022-09-20 08:39:09.326867+00	2022-09-20 08:39:09.326897+00	1	t	\N	f	f
1760	PROJECT	Project	Wapp Hardware Sales	247872	2022-09-20 08:39:09.326958+00	2022-09-20 08:39:09.326988+00	1	t	\N	f	f
1761	PROJECT	Project	Warnberg Automotive and Associates	247873	2022-09-20 08:39:09.327049+00	2022-09-20 08:39:09.327078+00	1	t	\N	f	f
1762	PROJECT	Project	Warwick Lumber	247874	2022-09-20 08:39:09.327139+00	2022-09-20 08:39:09.327168+00	1	t	\N	f	f
1763	PROJECT	Project	Wasager Wine Sales	247875	2022-09-20 08:39:09.327229+00	2022-09-20 08:39:09.327258+00	1	t	\N	f	f
1764	PROJECT	Project	Wassenaar Construction Services	247876	2022-09-20 08:39:09.327318+00	2022-09-20 08:39:09.327347+00	1	t	\N	f	f
1765	PROJECT	Project	Watertown Hicks	247877	2022-09-20 08:39:09.32741+00	2022-09-20 08:39:09.327586+00	1	t	\N	f	f
1766	PROJECT	Project	Weare and Norvell Painting Co.	247878	2022-09-20 08:39:09.327654+00	2022-09-20 08:39:09.327683+00	1	t	\N	f	f
1767	PROJECT	Project	Webmaster Gproxy	247879	2022-09-20 08:39:09.327744+00	2022-09-20 08:39:09.327773+00	1	t	\N	f	f
1768	PROJECT	Project	Webster Electric	247880	2022-09-20 08:39:09.327862+00	2022-09-20 08:39:09.327891+00	1	t	\N	f	f
1769	PROJECT	Project	Wedge Automotive Fabricators	247881	2022-09-20 08:39:09.327951+00	2022-09-20 08:39:09.328001+00	1	t	\N	f	f
1770	PROJECT	Project	Wenatchee Builders Fabricators	247882	2022-09-20 08:39:09.328174+00	2022-09-20 08:39:09.328226+00	1	t	\N	f	f
1771	PROJECT	Project	Wence Antiques Rentals	247883	2022-09-20 08:39:09.328529+00	2022-09-20 08:39:09.328733+00	1	t	\N	f	f
1772	PROJECT	Project	Wendler Markets Leasing	247884	2022-09-20 08:39:09.328852+00	2022-09-20 08:39:09.328902+00	1	t	\N	f	f
1773	PROJECT	Project	West Covina Builders Distributors	247885	2022-09-20 08:39:09.329014+00	2022-09-20 08:39:09.329047+00	1	t	\N	f	f
1774	PROJECT	Project	West Palm Beach Painting Manufacturing	247886	2022-09-20 08:39:09.329128+00	2022-09-20 08:39:09.329158+00	1	t	\N	f	f
1775	PROJECT	Project	Westminster Lumber Sales	247887	2022-09-20 08:39:09.329224+00	2022-09-20 08:39:09.329254+00	1	t	\N	f	f
1776	PROJECT	Project	Westminster Lumber Sales 1	247888	2022-09-20 08:39:09.32932+00	2022-09-20 08:39:09.329351+00	1	t	\N	f	f
1777	PROJECT	Project	Wethersfield Hardware Dynamics	247889	2022-09-20 08:39:09.329535+00	2022-09-20 08:39:09.329566+00	1	t	\N	f	f
1778	PROJECT	Project	Wettlaufer Construction Systems	247890	2022-09-20 08:39:09.329632+00	2022-09-20 08:39:09.329667+00	1	t	\N	f	f
1779	PROJECT	Project	Wever Apartments -	247891	2022-09-20 08:39:09.329732+00	2022-09-20 08:39:09.329762+00	1	t	\N	f	f
1780	PROJECT	Project	Whetzell and Maymon Antiques Sales	247892	2022-09-20 08:39:09.329835+00	2022-09-20 08:39:09.329862+00	1	t	\N	f	f
1781	PROJECT	Project	Whittier Hardware -	247893	2022-09-20 08:39:09.329921+00	2022-09-20 08:39:09.329948+00	1	t	\N	f	f
1782	PROJECT	Project	Whole Oats Markets	247894	2022-09-20 08:39:09.330016+00	2022-09-20 08:39:09.330088+00	1	t	\N	f	f
1783	PROJECT	Project	Wickenhauser Hardware Management	247895	2022-09-20 08:39:09.330189+00	2022-09-20 08:39:09.330217+00	1	t	\N	f	f
1784	PROJECT	Project	Wicklund Leasing Corporation	247896	2022-09-20 08:39:09.336943+00	2022-09-20 08:39:09.336995+00	1	t	\N	f	f
1785	PROJECT	Project	Wiesel Construction Dynamics	247897	2022-09-20 08:39:09.337063+00	2022-09-20 08:39:09.337092+00	1	t	\N	f	f
1786	PROJECT	Project	Wiggles Inc.	247898	2022-09-20 08:39:09.337152+00	2022-09-20 08:39:09.33718+00	1	t	\N	f	f
1787	PROJECT	Project	Wilkey Markets Group	247899	2022-09-20 08:39:09.337252+00	2022-09-20 08:39:09.337282+00	1	t	\N	f	f
1788	PROJECT	Project	Will's Leather Co.	247900	2022-09-20 08:39:09.337344+00	2022-09-20 08:39:09.337559+00	1	t	\N	f	f
1789	PROJECT	Project	Williams Electronics and Communications	247901	2022-09-20 08:39:09.337638+00	2022-09-20 08:39:09.337668+00	1	t	\N	f	f
1790	PROJECT	Project	Williams Wireless World	247902	2022-09-20 08:39:09.337732+00	2022-09-20 08:39:09.337761+00	1	t	\N	f	f
1791	PROJECT	Project	Wilner Liquors	247903	2022-09-20 08:39:09.337822+00	2022-09-20 08:39:09.337852+00	1	t	\N	f	f
1792	PROJECT	Project	Wilson Kaplan	247904	2022-09-20 08:39:09.337912+00	2022-09-20 08:39:09.337941+00	1	t	\N	f	f
1793	PROJECT	Project	Windisch Title Corporation	247905	2022-09-20 08:39:09.338003+00	2022-09-20 08:39:09.338032+00	1	t	\N	f	f
1794	PROJECT	Project	Witten Antiques Services	247906	2022-09-20 08:39:09.338092+00	2022-09-20 08:39:09.338121+00	1	t	\N	f	f
1795	PROJECT	Project	Wolfenden Markets Holding Corp.	247907	2022-09-20 08:39:09.338189+00	2022-09-20 08:39:09.338216+00	1	t	\N	f	f
1796	PROJECT	Project	Wollan Software Rentals	247908	2022-09-20 08:39:09.338273+00	2022-09-20 08:39:09.338301+00	1	t	\N	f	f
1797	PROJECT	Project	Wood Wonders Funiture	247909	2022-09-20 08:39:09.338462+00	2022-09-20 08:39:09.338494+00	1	t	\N	f	f
1798	PROJECT	Project	Wood-Mizer	247910	2022-09-20 08:39:09.338555+00	2022-09-20 08:39:09.33858+00	1	t	\N	f	f
1799	PROJECT	Project	Woods Publishing Co.	247911	2022-09-20 08:39:09.338629+00	2022-09-20 08:39:09.33865+00	1	t	\N	f	f
1800	PROJECT	Project	Woon Hardware Networking	247912	2022-09-20 08:39:09.338718+00	2022-09-20 08:39:09.338745+00	1	t	\N	f	f
1801	PROJECT	Project	Wraight Software and Associates	247913	2022-09-20 08:39:09.338803+00	2022-09-20 08:39:09.338829+00	1	t	\N	f	f
1802	PROJECT	Project	X Eye Corp	247914	2022-09-20 08:39:09.338897+00	2022-09-20 08:39:09.338926+00	1	t	\N	f	f
1803	PROJECT	Project	Y-Tec Manufacturing	247915	2022-09-20 08:39:09.338987+00	2022-09-20 08:39:09.339016+00	1	t	\N	f	f
1804	PROJECT	Project	Yahl Markets Incorporated	247916	2022-09-20 08:39:09.339072+00	2022-09-20 08:39:09.339092+00	1	t	\N	f	f
1805	PROJECT	Project	Yanity Apartments and Associates	247917	2022-09-20 08:39:09.339153+00	2022-09-20 08:39:09.339272+00	1	t	\N	f	f
1806	PROJECT	Project	Yarnell Catering Holding Corp.	247918	2022-09-20 08:39:09.339335+00	2022-09-20 08:39:09.339364+00	1	t	\N	f	f
1807	PROJECT	Project	Yockey Markets Inc.	247919	2022-09-20 08:39:09.339424+00	2022-09-20 08:39:09.339446+00	1	t	\N	f	f
1808	PROJECT	Project	Yong Yi	247920	2022-09-20 08:39:09.339505+00	2022-09-20 08:39:09.339528+00	1	t	\N	f	f
1809	PROJECT	Project	Yucca Valley Camping	247921	2022-09-20 08:39:09.339577+00	2022-09-20 08:39:09.339598+00	1	t	\N	f	f
1810	PROJECT	Project	Yucca Valley Title Agency	247922	2022-09-20 08:39:09.339659+00	2022-09-20 08:39:09.339688+00	1	t	\N	f	f
1811	PROJECT	Project	Zearfoss Windows Group	247923	2022-09-20 08:39:09.339747+00	2022-09-20 08:39:09.339768+00	1	t	\N	f	f
1812	PROJECT	Project	Zechiel _ Management	247924	2022-09-20 08:39:09.339822+00	2022-09-20 08:39:09.339937+00	1	t	\N	f	f
1813	PROJECT	Project	Zombro Telecom Leasing	247925	2022-09-20 08:39:09.33999+00	2022-09-20 08:39:09.340029+00	1	t	\N	f	f
1814	PROJECT	Project	Zucca Electric Agency	247926	2022-09-20 08:39:09.340086+00	2022-09-20 08:39:09.340113+00	1	t	\N	f	f
1815	PROJECT	Project	Zucconi Telecom Sales	247927	2022-09-20 08:39:09.340169+00	2022-09-20 08:39:09.340197+00	1	t	\N	f	f
1816	PROJECT	Project	Zurasky Markets Dynamics	247928	2022-09-20 08:39:09.340253+00	2022-09-20 08:39:09.34029+00	1	t	\N	f	f
1817	PROJECT	Project	eNable Corp	247929	2022-09-20 08:39:09.340464+00	2022-09-20 08:39:09.340495+00	1	t	\N	f	f
1818	PROJECT	Project	qa 54	247930	2022-09-20 08:39:09.340555+00	2022-09-20 08:39:09.340584+00	1	t	\N	f	f
1820	PROJECT	Project	tester1	247932	2022-09-20 08:39:09.340732+00	2022-09-20 08:39:09.340761+00	1	t	\N	f	f
1821	PROJECT	Project	ugkas	247933	2022-09-20 08:39:09.340821+00	2022-09-20 08:39:09.340849+00	1	t	\N	f	f
1822	PROJECT	Project	Company 1618550408	249071	2022-09-20 08:39:09.340909+00	2022-09-20 08:39:09.340938+00	1	t	\N	f	f
1823	PROJECT	Project	Company 1618566776	250488	2022-09-20 08:39:09.340998+00	2022-09-20 08:39:09.341027+00	1	t	\N	f	f
1824	PROJECT	Project	Project Red	251304	2022-09-20 08:39:09.341087+00	2022-09-20 08:39:09.341115+00	1	t	\N	f	f
1825	PROJECT	Project	Sravan Prod Test Prod	254098	2022-09-20 08:39:09.341175+00	2022-09-20 08:39:09.341204+00	1	t	\N	f	f
1826	PROJECT	Project	Ashwinn	254145	2022-09-20 08:39:09.341263+00	2022-09-20 08:39:09.341292+00	1	t	\N	f	f
1827	PROJECT	Project	Customer Sravan	274656	2022-09-20 08:39:09.341352+00	2022-09-20 08:39:09.341385+00	1	t	\N	f	f
1828	PROJECT	Project	Fyle Integrations	274657	2022-09-20 08:39:09.341501+00	2022-09-20 08:39:09.341531+00	1	t	\N	f	f
1829	PROJECT	Project	Fyle Nilesh	274658	2022-09-20 08:39:09.341592+00	2022-09-20 08:39:09.341621+00	1	t	\N	f	f
1830	PROJECT	Project	Nilesh	274659	2022-09-20 08:39:09.34178+00	2022-09-20 08:39:09.341844+00	1	t	\N	f	f
1831	PROJECT	Project	Brosey Antiques	278175	2022-09-20 08:39:09.342037+00	2022-09-20 08:39:09.342091+00	1	t	\N	f	f
1832	PROJECT	Project	Sample Test	278284	2022-09-20 08:39:09.342191+00	2022-09-20 08:39:09.342226+00	1	t	\N	f	f
1833	PROJECT	Project	Adwin Ko	278532	2022-09-20 08:39:09.342312+00	2022-09-20 08:39:09.342613+00	1	t	\N	f	f
1834	PROJECT	Project	Alex Blakey	278533	2022-09-20 08:39:09.539047+00	2022-09-20 08:39:09.53908+00	1	t	\N	f	f
1835	PROJECT	Project	Benjamin Yeung	278534	2022-09-20 08:39:09.539136+00	2022-09-20 08:39:09.539167+00	1	t	\N	f	f
1836	PROJECT	Project	Cathy Quon	278535	2022-09-20 08:39:09.539361+00	2022-09-20 08:39:09.539385+00	1	t	\N	f	f
1837	PROJECT	Project	Chadha's Consultants	278536	2022-09-20 08:39:09.539438+00	2022-09-20 08:39:09.539467+00	1	t	\N	f	f
1838	PROJECT	Project	Charlie Whitehead	278537	2022-09-20 08:39:09.539528+00	2022-09-20 08:39:09.53955+00	1	t	\N	f	f
1839	PROJECT	Project	Cheng-Cheng Lok	278538	2022-09-20 08:39:09.539602+00	2022-09-20 08:39:09.539631+00	1	t	\N	f	f
1840	PROJECT	Project	Clement's Cleaners	278539	2022-09-20 08:39:09.539691+00	2022-09-20 08:39:09.53972+00	1	t	\N	f	f
1841	PROJECT	Project	Ecker Designs	278540	2022-09-20 08:39:09.53978+00	2022-09-20 08:39:09.539802+00	1	t	\N	f	f
1842	PROJECT	Project	Froilan Rosqueta	278541	2022-09-20 08:39:09.539854+00	2022-09-20 08:39:09.539883+00	1	t	\N	f	f
1843	PROJECT	Project	Gorman Ho	278542	2022-09-20 08:39:09.539943+00	2022-09-20 08:39:09.539972+00	1	t	\N	f	f
1844	PROJECT	Project	Hazel Robinson	278543	2022-09-20 08:39:09.540032+00	2022-09-20 08:39:09.540054+00	1	t	\N	f	f
1845	PROJECT	Project	Himateja Madala	278544	2022-09-20 08:39:09.540105+00	2022-09-20 08:39:09.540134+00	1	t	\N	f	f
1846	PROJECT	Project	Jacint Tumacder	278545	2022-09-20 08:39:09.540309+00	2022-09-20 08:39:09.54034+00	1	t	\N	f	f
1847	PROJECT	Project	Jen Zaccarella	278546	2022-09-20 08:39:09.540392+00	2022-09-20 08:39:09.540413+00	1	t	\N	f	f
1848	PROJECT	Project	Jordan Burgess	278547	2022-09-20 08:39:09.540474+00	2022-09-20 08:39:09.540503+00	1	t	\N	f	f
1849	PROJECT	Project	Justine Outland	278548	2022-09-20 08:39:09.540555+00	2022-09-20 08:39:09.540574+00	1	t	\N	f	f
1850	PROJECT	Project	Kari Steblay	278549	2022-09-20 08:39:09.540622+00	2022-09-20 08:39:09.540643+00	1	t	\N	f	f
1851	PROJECT	Project	Karna Nisewaner	278550	2022-09-20 08:39:09.540687+00	2022-09-20 08:39:09.540708+00	1	t	\N	f	f
1852	PROJECT	Project	Kristy Abercrombie	278551	2022-09-20 08:39:09.540768+00	2022-09-20 08:39:09.540797+00	1	t	\N	f	f
1853	PROJECT	Project	Lew Plumbing	278552	2022-09-20 08:39:09.541607+00	2022-09-20 08:39:09.5417+00	1	t	\N	f	f
1854	PROJECT	Project	Moturu Tapasvi	278553	2022-09-20 08:39:09.541881+00	2022-09-20 08:39:09.541972+00	1	t	\N	f	f
1855	PROJECT	Project	Nadia Phillipchuk	278554	2022-09-20 08:39:09.542081+00	2022-09-20 08:39:09.542124+00	1	t	\N	f	f
1856	PROJECT	Project	Oxon Insurance Agency	278555	2022-09-20 08:39:09.542374+00	2022-09-20 08:39:09.542409+00	1	t	\N	f	f
1857	PROJECT	Project	Oxon Insurance Agency:Oxon -- Holiday Party	278556	2022-09-20 08:39:09.542538+00	2022-09-20 08:39:09.542641+00	1	t	\N	f	f
1858	PROJECT	Project	Oxon Insurance Agency:Oxon - Retreat	278557	2022-09-20 08:39:09.542773+00	2022-09-20 08:39:09.542819+00	1	t	\N	f	f
1859	PROJECT	Project	Rob deMontarnal	278558	2022-09-20 08:39:09.542932+00	2022-09-20 08:39:09.542981+00	1	t	\N	f	f
1871	PROJECT	Project	Attack on titans / Ackerman	290927	2022-09-20 08:39:09.547665+00	2022-09-20 08:39:09.547687+00	1	t	\N	f	f
1872	PROJECT	Project	MSD Project	292180	2022-09-20 08:39:09.548615+00	2022-09-20 08:39:09.548662+00	1	t	\N	f	f
1873	PROJECT	Project	Fast and Furious	292182	2022-09-20 08:39:09.548807+00	2022-09-20 08:39:09.548851+00	1	t	\N	f	f
688	PROJECT	Project	Fyle Engineering	243608	2022-09-20 08:39:06.869004+00	2022-09-20 08:39:06.86906+00	1	t	\N	t	f
1860	PROJECT	Project	Fixed Fee Project with Five Tasks	284355	2022-09-20 08:39:09.543086+00	2022-09-20 08:39:09.544981+00	1	t	\N	t	f
1861	PROJECT	Project	Fyle NetSuite Integration	284356	2022-09-20 08:39:09.545129+00	2022-09-20 08:39:09.545173+00	1	t	\N	t	f
1862	PROJECT	Project	Fyle Sage Intacct Integration	284357	2022-09-20 08:39:09.545518+00	2022-09-20 08:39:09.545565+00	1	t	\N	t	f
1863	PROJECT	Project	General Overhead	284358	2022-09-20 08:39:09.545645+00	2022-09-20 08:39:09.546619+00	1	t	\N	t	f
1864	PROJECT	Project	General Overhead-Current	284359	2022-09-20 08:39:09.546745+00	2022-09-20 08:39:09.546781+00	1	t	\N	t	f
1865	PROJECT	Project	Integrations	284360	2022-09-20 08:39:09.546879+00	2022-09-20 08:39:09.546914+00	1	t	\N	t	f
1866	PROJECT	Project	Mobile App Redesign	284361	2022-09-20 08:39:09.547005+00	2022-09-20 08:39:09.54705+00	1	t	\N	t	f
1867	PROJECT	Project	Platform APIs	284362	2022-09-20 08:39:09.547165+00	2022-09-20 08:39:09.547192+00	1	t	\N	t	f
1868	PROJECT	Project	Support Taxes	284363	2022-09-20 08:39:09.547342+00	2022-09-20 08:39:09.547362+00	1	t	\N	t	f
1869	PROJECT	Project	T&M Project with Five Tasks	284364	2022-09-20 08:39:09.547423+00	2022-09-20 08:39:09.547462+00	1	t	\N	t	f
1870	PROJECT	Project	labhvam	290031	2022-09-20 08:39:09.547574+00	2022-09-20 08:39:09.547604+00	1	t	\N	t	f
3218	PROJECT	Project	Branding Analysis	304665	2022-09-20 08:40:25.829933+00	2022-09-20 08:40:25.830111+00	1	t	\N	t	f
3219	PROJECT	Project	Branding Follow Up	304666	2022-09-20 08:40:25.832021+00	2022-09-20 08:40:25.832103+00	1	t	\N	t	f
3220	PROJECT	Project	Direct Mail Campaign	304667	2022-09-20 08:40:25.834913+00	2022-09-20 08:40:25.83498+00	1	t	\N	t	f
3221	PROJECT	Project	Ecommerce Campaign	304668	2022-09-20 08:40:25.835186+00	2022-09-20 08:40:25.835223+00	1	t	\N	t	f
2440	SYSTEM_OPERATING	System Operating	Support-M	expense_custom_field.system operating.1	2022-09-20 08:39:10.752946+00	2022-09-20 08:39:10.752986+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2441	SYSTEM_OPERATING	System Operating	GB3-White	expense_custom_field.system operating.2	2022-09-20 08:39:10.753043+00	2022-09-20 08:39:10.753065+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2442	SYSTEM_OPERATING	System Operating	TSM - Black	expense_custom_field.system operating.3	2022-09-20 08:39:10.753128+00	2022-09-20 08:39:10.759395+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2443	SYSTEM_OPERATING	System Operating	GB1-White	expense_custom_field.system operating.4	2022-09-20 08:39:10.768644+00	2022-09-20 08:39:10.768789+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2444	SYSTEM_OPERATING	System Operating	DevD	expense_custom_field.system operating.5	2022-09-20 08:39:10.768964+00	2022-09-20 08:39:10.769008+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2445	SYSTEM_OPERATING	System Operating	DevH	expense_custom_field.system operating.6	2022-09-20 08:39:10.769123+00	2022-09-20 08:39:10.769164+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2446	SYSTEM_OPERATING	System Operating	PMBr	expense_custom_field.system operating.7	2022-09-20 08:39:10.769733+00	2022-09-20 08:39:10.769797+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2447	SYSTEM_OPERATING	System Operating	octane squad	expense_custom_field.system operating.8	2022-09-20 08:39:10.769952+00	2022-09-20 08:39:10.769998+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2448	SYSTEM_OPERATING	System Operating	PMD	expense_custom_field.system operating.9	2022-09-20 08:39:10.770144+00	2022-09-20 08:39:10.77035+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2449	SYSTEM_OPERATING	System Operating	wraith squad	expense_custom_field.system operating.10	2022-09-20 08:39:10.770559+00	2022-09-20 08:39:10.770612+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2450	SYSTEM_OPERATING	System Operating	PMDD	expense_custom_field.system operating.11	2022-09-20 08:39:10.770767+00	2022-09-20 08:39:10.771407+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2451	SYSTEM_OPERATING	System Operating	BOOK	expense_custom_field.system operating.12	2022-09-20 08:39:10.771814+00	2022-09-20 08:39:10.77186+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2452	SYSTEM_OPERATING	System Operating	GB9-White	expense_custom_field.system operating.13	2022-09-20 08:39:10.772466+00	2022-09-20 08:39:10.772538+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2453	SYSTEM_OPERATING	System Operating	TSS - Black	expense_custom_field.system operating.14	2022-09-20 08:39:10.772743+00	2022-09-20 08:39:10.7728+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2454	SYSTEM_OPERATING	System Operating	PMWe	expense_custom_field.system operating.15	2022-09-20 08:39:10.773822+00	2022-09-20 08:39:10.773916+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2455	SYSTEM_OPERATING	System Operating	TSL - Black	expense_custom_field.system operating.16	2022-09-20 08:39:10.774574+00	2022-09-20 08:39:10.774624+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2456	SYSTEM_OPERATING	System Operating	Train-MS	expense_custom_field.system operating.17	2022-09-20 08:39:10.774731+00	2022-09-20 08:39:10.774783+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2457	SYSTEM_OPERATING	System Operating	GB6-White	expense_custom_field.system operating.18	2022-09-20 08:39:10.775079+00	2022-09-20 08:39:10.775183+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2458	SYSTEM_OPERATING	System Operating	naruto uzumaki	expense_custom_field.system operating.19	2022-09-20 08:39:10.7759+00	2022-09-20 08:39:10.77663+00	1	\N	{"placeholder": "Select System Operating", "is_dependent": false, "custom_field_id": 174995}	f	f
2459	TEAM	Team	CCC	expense_custom_field.team.1	2022-09-20 08:39:10.823717+00	2022-09-20 08:39:10.824018+00	1	\N	{"placeholder": "Select Team", "is_dependent": false, "custom_field_id": 174175}	f	f
2460	TEAM	Team	Integrations	expense_custom_field.team.2	2022-09-20 08:39:10.824396+00	2022-09-20 08:39:10.824443+00	1	\N	{"placeholder": "Select Team", "is_dependent": false, "custom_field_id": 174175}	f	f
2461	USER_DIMENSION_COPY	User Dimension Copy	Wedding Planning by Whitney	expense_custom_field.user dimension copy.1	2022-09-20 08:39:10.841239+00	2022-09-20 08:39:10.841279+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2462	USER_DIMENSION_COPY	User Dimension Copy	Dylan Sollfrank	expense_custom_field.user dimension copy.2	2022-09-20 08:39:10.841361+00	2022-09-20 08:39:10.841384+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2463	USER_DIMENSION_COPY	User Dimension Copy	Admin	expense_custom_field.user dimension copy.3	2022-09-20 08:39:10.841843+00	2022-09-20 08:39:10.841866+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2464	USER_DIMENSION_COPY	User Dimension Copy	Production	expense_custom_field.user dimension copy.4	2022-09-20 08:39:10.841925+00	2022-09-20 08:39:10.841946+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2465	USER_DIMENSION_COPY	User Dimension Copy	Fyle	expense_custom_field.user dimension copy.5	2022-09-20 08:39:10.842016+00	2022-09-20 08:39:10.842046+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2466	USER_DIMENSION_COPY	User Dimension Copy	Diego Rodriguez	expense_custom_field.user dimension copy.6	2022-09-20 08:39:10.842115+00	2022-09-20 08:39:10.842145+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2467	USER_DIMENSION_COPY	User Dimension Copy	wraith squad	expense_custom_field.user dimension copy.7	2022-09-20 08:39:10.842214+00	2022-09-20 08:39:10.842642+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2468	USER_DIMENSION_COPY	User Dimension Copy	Ashwinn	expense_custom_field.user dimension copy.8	2022-09-20 08:39:10.842746+00	2022-09-20 08:39:10.842769+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2469	USER_DIMENSION_COPY	User Dimension Copy	Geeta Kalapatapu	expense_custom_field.user dimension copy.9	2022-09-20 08:39:10.842833+00	2022-09-20 08:39:10.842862+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2470	USER_DIMENSION_COPY	User Dimension Copy	naruto uzumaki	expense_custom_field.user dimension copy.10	2022-09-20 08:39:10.842931+00	2022-09-20 08:39:10.84296+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2532	DEPARTMENTS	Departments	IT	expense_custom_field.departments.3	2022-09-20 08:39:10.918729+00	2022-09-20 08:39:10.918799+00	1	\N	{"placeholder": "Select Departments", "is_dependent": false, "custom_field_id": 174997}	f	f
2471	USER_DIMENSION_COPY	User Dimension Copy	Travis Waldron	expense_custom_field.user dimension copy.11	2022-09-20 08:39:10.843123+00	2022-09-20 08:39:10.843157+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2472	USER_DIMENSION_COPY	User Dimension Copy	Weiskopf Consulting	expense_custom_field.user dimension copy.12	2022-09-20 08:39:10.843227+00	2022-09-20 08:39:10.843254+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2473	USER_DIMENSION_COPY	User Dimension Copy	Dukes Basketball Camp	expense_custom_field.user dimension copy.13	2022-09-20 08:39:10.843307+00	2022-09-20 08:39:10.843328+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2474	USER_DIMENSION_COPY	User Dimension Copy	Product	expense_custom_field.user dimension copy.14	2022-09-20 08:39:10.843402+00	2022-09-20 08:39:10.843432+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2475	USER_DIMENSION_COPY	User Dimension Copy	Mark Cho	expense_custom_field.user dimension copy.15	2022-09-20 08:39:10.844001+00	2022-09-20 08:39:10.844035+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2476	USER_DIMENSION_COPY	User Dimension Copy	Sushi by Katsuyuki	expense_custom_field.user dimension copy.16	2022-09-20 08:39:10.84414+00	2022-09-20 08:39:10.844161+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2477	USER_DIMENSION_COPY	User Dimension Copy	Diego Rodriguez:Test Project	expense_custom_field.user dimension copy.17	2022-09-20 08:39:10.844328+00	2022-09-20 08:39:10.844377+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2478	USER_DIMENSION_COPY	User Dimension Copy	Sales	expense_custom_field.user dimension copy.18	2022-09-20 08:39:10.844501+00	2022-09-20 08:39:10.844543+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2479	USER_DIMENSION_COPY	User Dimension Copy	Pye's Cakes	expense_custom_field.user dimension copy.19	2022-09-20 08:39:10.845209+00	2022-09-20 08:39:10.845279+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2480	USER_DIMENSION_COPY	User Dimension Copy	Assembly	expense_custom_field.user dimension copy.20	2022-09-20 08:39:10.845433+00	2022-09-20 08:39:10.84548+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2481	USER_DIMENSION_COPY	User Dimension Copy	Freeman Sporting Goods:55 Twin Lane	expense_custom_field.user dimension copy.21	2022-09-20 08:39:10.845613+00	2022-09-20 08:39:10.845654+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2482	USER_DIMENSION_COPY	User Dimension Copy	Machine Shop	expense_custom_field.user dimension copy.22	2022-09-20 08:39:10.845779+00	2022-09-20 08:39:10.845821+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2483	USER_DIMENSION_COPY	User Dimension Copy	Kookies by Kathy	expense_custom_field.user dimension copy.23	2022-09-20 08:39:10.84595+00	2022-09-20 08:39:10.845992+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2586	CLASS	Class	Dylan Sollfrank	expense_custom_field.class.3	2022-09-20 08:39:10.963386+00	2022-09-20 08:39:10.963414+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2484	USER_DIMENSION_COPY	User Dimension Copy	Shara Barnett:Barnett Design	expense_custom_field.user dimension copy.24	2022-09-20 08:39:10.846113+00	2022-09-20 08:39:10.846162+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2485	USER_DIMENSION_COPY	User Dimension Copy	Amy's Bird Sanctuary	expense_custom_field.user dimension copy.25	2022-09-20 08:39:10.846296+00	2022-09-20 08:39:10.846337+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2517	LOCATION	Location	Australia	expense_custom_field.location.5	2022-09-20 08:39:10.894617+00	2022-09-20 08:39:10.894661+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2486	USER_DIMENSION_COPY	User Dimension Copy	Amy's Bird Sanctuary:Test Project	expense_custom_field.user dimension copy.26	2022-09-20 08:39:10.846451+00	2022-09-20 08:39:10.846497+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2487	USER_DIMENSION_COPY	User Dimension Copy	Gevelber Photography	expense_custom_field.user dimension copy.27	2022-09-20 08:39:10.846918+00	2022-09-20 08:39:10.847145+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2488	USER_DIMENSION_COPY	User Dimension Copy	Red Rock Diner	expense_custom_field.user dimension copy.28	2022-09-20 08:39:10.847412+00	2022-09-20 08:39:10.84782+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2489	USER_DIMENSION_COPY	User Dimension Copy	Fabrication	expense_custom_field.user dimension copy.29	2022-09-20 08:39:10.847937+00	2022-09-20 08:39:10.847967+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2490	USER_DIMENSION_COPY	User Dimension Copy	Cool Cars	expense_custom_field.user dimension copy.30	2022-09-20 08:39:10.848037+00	2022-09-20 08:39:10.848058+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2491	USER_DIMENSION_COPY	User Dimension Copy	octane squad	expense_custom_field.user dimension copy.31	2022-09-20 08:39:10.848126+00	2022-09-20 08:39:10.848146+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2492	USER_DIMENSION_COPY	User Dimension Copy	Sravan BLR Customer	expense_custom_field.user dimension copy.32	2022-09-20 08:39:10.848317+00	2022-09-20 08:39:10.848347+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2493	USER_DIMENSION_COPY	User Dimension Copy	Rago Travel Agency	expense_custom_field.user dimension copy.33	2022-09-20 08:39:10.848425+00	2022-09-20 08:39:10.848466+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2494	USER_DIMENSION_COPY	User Dimension Copy	Marketing	expense_custom_field.user dimension copy.34	2022-09-20 08:39:10.8487+00	2022-09-20 08:39:10.848719+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2495	USER_DIMENSION_COPY	User Dimension Copy	John Melton	expense_custom_field.user dimension copy.35	2022-09-20 08:39:10.848768+00	2022-09-20 08:39:10.848789+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2496	USER_DIMENSION_COPY	User Dimension Copy	Inspection	expense_custom_field.user dimension copy.36	2022-09-20 08:39:10.849628+00	2022-09-20 08:39:10.849676+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2497	USER_DIMENSION_COPY	User Dimension Copy	Bill's Windsurf Shop	expense_custom_field.user dimension copy.37	2022-09-20 08:39:10.849904+00	2022-09-20 08:39:10.849946+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2534	DEPARTMENTS	Departments	Admin	expense_custom_field.departments.5	2022-09-20 08:39:10.919259+00	2022-09-20 08:39:10.919285+00	1	\N	{"placeholder": "Select Departments", "is_dependent": false, "custom_field_id": 174997}	f	f
2498	USER_DIMENSION_COPY	User Dimension Copy	Paulsen Medical Supplies	expense_custom_field.user dimension copy.38	2022-09-20 08:39:10.850109+00	2022-09-20 08:39:10.850578+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2499	USER_DIMENSION_COPY	User Dimension Copy	Kate Whelan	expense_custom_field.user dimension copy.39	2022-09-20 08:39:10.850781+00	2022-09-20 08:39:10.850809+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2500	USER_DIMENSION_COPY	User Dimension Copy	Freeman Sporting Goods:0969 Ocean View Road	expense_custom_field.user dimension copy.40	2022-09-20 08:39:10.850893+00	2022-09-20 08:39:10.850921+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2501	USER_DIMENSION_COPY	User Dimension Copy	Freeman Sporting Goods	expense_custom_field.user dimension copy.41	2022-09-20 08:39:10.850978+00	2022-09-20 08:39:10.850999+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2502	USER_DIMENSION_COPY	User Dimension Copy	Rondonuwu Fruit and Vegi	expense_custom_field.user dimension copy.42	2022-09-20 08:39:10.851058+00	2022-09-20 08:39:10.851074+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2503	USER_DIMENSION_COPY	User Dimension Copy	Shara Barnett	expense_custom_field.user dimension copy.43	2022-09-20 08:39:10.851145+00	2022-09-20 08:39:10.851351+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2504	USER_DIMENSION_COPY	User Dimension Copy	Video Games by Dan	expense_custom_field.user dimension copy.44	2022-09-20 08:39:10.851575+00	2022-09-20 08:39:10.851654+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2505	USER_DIMENSION_COPY	User Dimension Copy	Service	expense_custom_field.user dimension copy.45	2022-09-20 08:39:10.851748+00	2022-09-20 08:39:10.851781+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2506	USER_DIMENSION_COPY	User Dimension Copy	Engineering	expense_custom_field.user dimension copy.46	2022-09-20 08:39:10.851863+00	2022-09-20 08:39:10.851885+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2507	USER_DIMENSION_COPY	User Dimension Copy	Jeff's Jalopies	expense_custom_field.user dimension copy.47	2022-09-20 08:39:10.851945+00	2022-09-20 08:39:10.851965+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2508	USER_DIMENSION_COPY	User Dimension Copy	Sonnenschein Family Store	expense_custom_field.user dimension copy.48	2022-09-20 08:39:10.852026+00	2022-09-20 08:39:10.852063+00	1	\N	{"placeholder": "Select User Dimension Copy", "is_dependent": false, "custom_field_id": 174991}	f	f
2509	OPERATING_SYSTEM	Operating System	India	expense_custom_field.operating system.1	2022-09-20 08:39:10.877424+00	2022-09-20 08:39:10.877464+00	1	\N	{"placeholder": "Select Operating System", "is_dependent": false, "custom_field_id": 133433}	f	f
2510	OPERATING_SYSTEM	Operating System	USA1	expense_custom_field.operating system.2	2022-09-20 08:39:10.877535+00	2022-09-20 08:39:10.877557+00	1	\N	{"placeholder": "Select Operating System", "is_dependent": false, "custom_field_id": 133433}	f	f
2511	OPERATING_SYSTEM	Operating System	USA2	expense_custom_field.operating system.3	2022-09-20 08:39:10.877626+00	2022-09-20 08:39:10.877646+00	1	\N	{"placeholder": "Select Operating System", "is_dependent": false, "custom_field_id": 133433}	f	f
2512	OPERATING_SYSTEM	Operating System	USA3	expense_custom_field.operating system.4	2022-09-20 08:39:10.877703+00	2022-09-20 08:39:10.877733+00	1	\N	{"placeholder": "Select Operating System", "is_dependent": false, "custom_field_id": 133433}	f	f
2513	LOCATION	Location	South Africa	expense_custom_field.location.1	2022-09-20 08:39:10.893887+00	2022-09-20 08:39:10.893935+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2514	LOCATION	Location	Bangalore	expense_custom_field.location.2	2022-09-20 08:39:10.894017+00	2022-09-20 08:39:10.89404+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2515	LOCATION	Location	London	expense_custom_field.location.3	2022-09-20 08:39:10.894328+00	2022-09-20 08:39:10.89437+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2516	LOCATION	Location	New South Wales	expense_custom_field.location.4	2022-09-20 08:39:10.894475+00	2022-09-20 08:39:10.894508+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2518	LOCATION	Location	naruto uzumaki	expense_custom_field.location.6	2022-09-20 08:39:10.894748+00	2022-09-20 08:39:10.894776+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2519	LOCATION	Location	octane squad	expense_custom_field.location.7	2022-09-20 08:39:10.894841+00	2022-09-20 08:39:10.89487+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2520	LOCATION	Location	Holding Company	expense_custom_field.location.8	2022-09-20 08:39:10.894965+00	2022-09-20 08:39:10.895295+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2521	LOCATION	Location	USA 1	expense_custom_field.location.9	2022-09-20 08:39:10.895395+00	2022-09-20 08:39:10.895418+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2522	LOCATION	Location	Elimination - Sub	expense_custom_field.location.10	2022-09-20 08:39:10.89549+00	2022-09-20 08:39:10.895927+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2523	LOCATION	Location	wraith squad	expense_custom_field.location.11	2022-09-20 08:39:10.896367+00	2022-09-20 08:39:10.896398+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2524	LOCATION	Location	USA 2	expense_custom_field.location.12	2022-09-20 08:39:10.896587+00	2022-09-20 08:39:10.896709+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2525	LOCATION	Location	Elimination - Global	expense_custom_field.location.13	2022-09-20 08:39:10.896802+00	2022-09-20 08:39:10.896834+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2526	LOCATION	Location	India	expense_custom_field.location.14	2022-09-20 08:39:10.896903+00	2022-09-20 08:39:10.896922+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2527	LOCATION	Location	Elimination - NA	expense_custom_field.location.15	2022-09-20 08:39:10.896969+00	2022-09-20 08:39:10.896981+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2528	LOCATION	Location	Canada	expense_custom_field.location.16	2022-09-20 08:39:10.897037+00	2022-09-20 08:39:10.897058+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2529	LOCATION	Location	United Kingdom	expense_custom_field.location.17	2022-09-20 08:39:10.897135+00	2022-09-20 08:39:10.89716+00	1	\N	{"placeholder": "Select Location", "is_dependent": false, "custom_field_id": 845}	f	f
2530	DEPARTMENTS	Departments	Services	expense_custom_field.departments.1	2022-09-20 08:39:10.918377+00	2022-09-20 08:39:10.918564+00	1	\N	{"placeholder": "Select Departments", "is_dependent": false, "custom_field_id": 174997}	f	f
2531	DEPARTMENTS	Departments	Sales	expense_custom_field.departments.2	2022-09-20 08:39:10.918639+00	2022-09-20 08:39:10.918662+00	1	\N	{"placeholder": "Select Departments", "is_dependent": false, "custom_field_id": 174997}	f	f
2533	DEPARTMENTS	Departments	Marketing	expense_custom_field.departments.4	2022-09-20 08:39:10.918962+00	2022-09-20 08:39:10.91917+00	1	\N	{"placeholder": "Select Departments", "is_dependent": false, "custom_field_id": 174997}	f	f
2535	TEAM_COPY	Team Copy	General Overhead-Current	expense_custom_field.team copy.1	2022-09-20 08:39:10.933098+00	2022-09-20 08:39:10.933126+00	1	\N	{"placeholder": "Select Team Copy", "is_dependent": false, "custom_field_id": 174993}	f	f
2536	TEAM_COPY	Team Copy	General Overhead	expense_custom_field.team copy.2	2022-09-20 08:39:10.933178+00	2022-09-20 08:39:10.933201+00	1	\N	{"placeholder": "Select Team Copy", "is_dependent": false, "custom_field_id": 174993}	f	f
2537	TEAM_COPY	Team Copy	Fyle Sage Intacct Integration	expense_custom_field.team copy.3	2022-09-20 08:39:10.933343+00	2022-09-20 08:39:10.933366+00	1	\N	{"placeholder": "Select Team Copy", "is_dependent": false, "custom_field_id": 174993}	f	f
2538	TEAM_COPY	Team Copy	Integrations	expense_custom_field.team copy.4	2022-09-20 08:39:10.933425+00	2022-09-20 08:39:10.933446+00	1	\N	{"placeholder": "Select Team Copy", "is_dependent": false, "custom_field_id": 174993}	f	f
2539	TEAM_COPY	Team Copy	Fyle Engineering	expense_custom_field.team copy.5	2022-09-20 08:39:10.933516+00	2022-09-20 08:39:10.933545+00	1	\N	{"placeholder": "Select Team Copy", "is_dependent": false, "custom_field_id": 174993}	f	f
2540	TEAM_COPY	Team Copy	Platform APIs	expense_custom_field.team copy.6	2022-09-20 08:39:10.933614+00	2022-09-20 08:39:10.933643+00	1	\N	{"placeholder": "Select Team Copy", "is_dependent": false, "custom_field_id": 174993}	f	f
2541	TEAM_COPY	Team Copy	Support Taxes	expense_custom_field.team copy.7	2022-09-20 08:39:10.933712+00	2022-09-20 08:39:10.933737+00	1	\N	{"placeholder": "Select Team Copy", "is_dependent": false, "custom_field_id": 174993}	f	f
2542	TEAM_COPY	Team Copy	labhvam	expense_custom_field.team copy.8	2022-09-20 08:39:10.933797+00	2022-09-20 08:39:10.933827+00	1	\N	{"placeholder": "Select Team Copy", "is_dependent": false, "custom_field_id": 174993}	f	f
2543	TEAM_COPY	Team Copy	Fyle NetSuite Integration	expense_custom_field.team copy.9	2022-09-20 08:39:10.933895+00	2022-09-20 08:39:10.933924+00	1	\N	{"placeholder": "Select Team Copy", "is_dependent": false, "custom_field_id": 174993}	f	f
2544	TEAM_COPY	Team Copy	T&M Project with Five Tasks	expense_custom_field.team copy.10	2022-09-20 08:39:10.933982+00	2022-09-20 08:39:10.933993+00	1	\N	{"placeholder": "Select Team Copy", "is_dependent": false, "custom_field_id": 174993}	f	f
2545	TEAM_COPY	Team Copy	Fixed Fee Project with Five Tasks	expense_custom_field.team copy.11	2022-09-20 08:39:10.934048+00	2022-09-20 08:39:10.934078+00	1	\N	{"placeholder": "Select Team Copy", "is_dependent": false, "custom_field_id": 174993}	f	f
2546	TEAM_COPY	Team Copy	Mobile App Redesign	expense_custom_field.team copy.12	2022-09-20 08:39:10.934146+00	2022-09-20 08:39:10.934176+00	1	\N	{"placeholder": "Select Team Copy", "is_dependent": false, "custom_field_id": 174993}	f	f
2584	CLASS	Class	goat	expense_custom_field.class.1	2022-09-20 08:39:10.963066+00	2022-09-20 08:39:10.963106+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2585	CLASS	Class	Diego Rodriguez	expense_custom_field.class.2	2022-09-20 08:39:10.963175+00	2022-09-20 08:39:10.963203+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2587	CLASS	Class	Rondonuwu Fruit and Vegi	expense_custom_field.class.4	2022-09-20 08:39:10.963476+00	2022-09-20 08:39:10.963515+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2588	CLASS	Class	Bill's Windsurf Shop	expense_custom_field.class.5	2022-09-20 08:39:10.963601+00	2022-09-20 08:39:10.963639+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2589	CLASS	Class	Kate Whelan	expense_custom_field.class.6	2022-09-20 08:39:10.964058+00	2022-09-20 08:39:10.964089+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2590	CLASS	Class	Mark Cho	expense_custom_field.class.7	2022-09-20 08:39:10.96443+00	2022-09-20 08:39:10.96458+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2591	CLASS	Class	Shara Barnett	expense_custom_field.class.8	2022-09-20 08:39:10.964777+00	2022-09-20 08:39:10.964799+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2592	CLASS	Class	Shara Barnett:Barnett Design	expense_custom_field.class.9	2022-09-20 08:39:10.964976+00	2022-09-20 08:39:10.965004+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2593	CLASS	Class	Kookies by Kathy	expense_custom_field.class.10	2022-09-20 08:39:10.965069+00	2022-09-20 08:39:10.965096+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2594	CLASS	Class	Weiskopf Consulting	expense_custom_field.class.11	2022-09-20 08:39:10.965161+00	2022-09-20 08:39:10.965188+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2595	CLASS	Class	Red Rock Diner	expense_custom_field.class.12	2022-09-20 08:39:10.965264+00	2022-09-20 08:39:10.965399+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2596	CLASS	Class	Freeman Sporting Goods:0969 Ocean View Road	expense_custom_field.class.13	2022-09-20 08:39:10.965475+00	2022-09-20 08:39:10.965502+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2597	CLASS	Class	John Melton	expense_custom_field.class.14	2022-09-20 08:39:10.965567+00	2022-09-20 08:39:10.965594+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2598	CLASS	Class	Dukes Basketball Camp	expense_custom_field.class.15	2022-09-20 08:39:10.965658+00	2022-09-20 08:39:10.965685+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2599	CLASS	Class	Sonnenschein Family Store	expense_custom_field.class.16	2022-09-20 08:39:10.965749+00	2022-09-20 08:39:10.965776+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2600	CLASS	Class	octane squad	expense_custom_field.class.17	2022-09-20 08:39:10.96584+00	2022-09-20 08:39:10.965867+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2601	CLASS	Class	Video Games by Dan	expense_custom_field.class.18	2022-09-20 08:39:10.965931+00	2022-09-20 08:39:10.965959+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2602	CLASS	Class	Jeff's Jalopies	expense_custom_field.class.19	2022-09-20 08:39:10.966023+00	2022-09-20 08:39:10.96605+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2603	CLASS	Class	Wedding Planning by Whitney	expense_custom_field.class.20	2022-09-20 08:39:10.966114+00	2022-09-20 08:39:10.966142+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2604	CLASS	Class	Pye's Cakes	expense_custom_field.class.21	2022-09-20 08:39:10.966206+00	2022-09-20 08:39:10.966233+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2605	CLASS	Class	Freeman Sporting Goods	expense_custom_field.class.22	2022-09-20 08:39:10.966298+00	2022-09-20 08:39:10.966325+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2606	CLASS	Class	wraith squad	expense_custom_field.class.23	2022-09-20 08:39:10.966513+00	2022-09-20 08:39:10.966544+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2607	CLASS	Class	Rago Travel Agency	expense_custom_field.class.24	2022-09-20 08:39:10.966621+00	2022-09-20 08:39:10.966649+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2608	CLASS	Class	Geeta Kalapatapu	expense_custom_field.class.25	2022-09-20 08:39:10.966714+00	2022-09-20 08:39:10.966741+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2609	CLASS	Class	Freeman Sporting Goods:55 Twin Lane	expense_custom_field.class.26	2022-09-20 08:39:10.966805+00	2022-09-20 08:39:10.966832+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2610	CLASS	Class	Travis Waldron	expense_custom_field.class.27	2022-09-20 08:39:10.966896+00	2022-09-20 08:39:10.966937+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2611	CLASS	Class	Amy's Bird Sanctuary	expense_custom_field.class.28	2022-09-20 08:39:10.967006+00	2022-09-20 08:39:10.967035+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2612	CLASS	Class	Sushi by Katsuyuki	expense_custom_field.class.29	2022-09-20 08:39:10.967104+00	2022-09-20 08:39:10.967133+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2613	CLASS	Class	Cool Cars	expense_custom_field.class.30	2022-09-20 08:39:10.967202+00	2022-09-20 08:39:10.967231+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2614	CLASS	Class	naruto uzumaki	expense_custom_field.class.31	2022-09-20 08:39:10.967404+00	2022-09-20 08:39:10.967445+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2615	CLASS	Class	Paulsen Medical Supplies	expense_custom_field.class.32	2022-09-20 08:39:10.967513+00	2022-09-20 08:39:10.967541+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2616	CLASS	Class	Gevelber Photography	expense_custom_field.class.33	2022-09-20 08:39:10.967605+00	2022-09-20 08:39:10.967633+00	1	\N	{"placeholder": "Select Class", "is_dependent": false, "custom_field_id": 190717}	f	f
2617	USER_DIMENSION	User Dimension	Services	expense_custom_field.user dimension.1	2022-09-20 08:39:10.980758+00	2022-09-20 08:39:10.980797+00	1	\N	{"placeholder": "Select User Dimension", "is_dependent": false, "custom_field_id": 174176}	f	f
2618	USER_DIMENSION	User Dimension	Sales	expense_custom_field.user dimension.2	2022-09-20 08:39:10.980866+00	2022-09-20 08:39:10.980894+00	1	\N	{"placeholder": "Select User Dimension", "is_dependent": false, "custom_field_id": 174176}	f	f
2619	USER_DIMENSION	User Dimension	Marketing	expense_custom_field.user dimension.3	2022-09-20 08:39:10.98096+00	2022-09-20 08:39:10.980988+00	1	\N	{"placeholder": "Select User Dimension", "is_dependent": false, "custom_field_id": 174176}	f	f
2620	USER_DIMENSION	User Dimension	Admin	expense_custom_field.user dimension.4	2022-09-20 08:39:10.981052+00	2022-09-20 08:39:10.98108+00	1	\N	{"placeholder": "Select User Dimension", "is_dependent": false, "custom_field_id": 174176}	f	f
2621	USER_DIMENSION	User Dimension	IT	expense_custom_field.user dimension.5	2022-09-20 08:39:10.981144+00	2022-09-20 08:39:10.981171+00	1	\N	{"placeholder": "Select User Dimension", "is_dependent": false, "custom_field_id": 174176}	f	f
2660	TAX_GROUPS	Tax Groups	Exempt Sales @0.0%	expense_custom_field.tax groups.1	2022-09-20 08:39:11.012135+00	2022-09-20 08:39:11.012188+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2661	TAX_GROUPS	Tax Groups	MB - GST/RST on Purchases @12.0%	expense_custom_field.tax groups.2	2022-09-20 08:39:11.012267+00	2022-09-20 08:39:11.012297+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2662	TAX_GROUPS	Tax Groups	MB - GST/RST on Sales @12.0%	expense_custom_field.tax groups.3	2022-09-20 08:39:11.012367+00	2022-09-20 08:39:11.012398+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2663	TAX_GROUPS	Tax Groups	Oakdale Sales Tax @8.125%	expense_custom_field.tax groups.4	2022-09-20 08:39:11.012589+00	2022-09-20 08:39:11.012619+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2664	TAX_GROUPS	Tax Groups	Sales Tax on Imports @0.0%	expense_custom_field.tax groups.5	2022-09-20 08:39:11.012691+00	2022-09-20 08:39:11.01272+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2665	TAX_GROUPS	Tax Groups	Tax Exempt @0.0%	expense_custom_field.tax groups.6	2022-09-20 08:39:11.012792+00	2022-09-20 08:39:11.012822+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2666	TAX_GROUPS	Tax Groups	Tax on Consulting @8.25%	expense_custom_field.tax groups.7	2022-09-20 08:39:11.012892+00	2022-09-20 08:39:11.012921+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2667	TAX_GROUPS	Tax Groups	Tax on Goods @8.75%	expense_custom_field.tax groups.8	2022-09-20 08:39:11.012991+00	2022-09-20 08:39:11.013047+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2668	TAX_GROUPS	Tax Groups	Tax on Goodss @8.125%	expense_custom_field.tax groups.9	2022-09-20 08:39:11.013119+00	2022-09-20 08:39:11.013158+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2669	TAX_GROUPS	Tax Groups	Tax on Purchases @8.25%	expense_custom_field.tax groups.10	2022-09-20 08:39:11.013351+00	2022-09-20 08:39:11.013383+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2670	TAX_GROUPS	Tax Groups	tax for working @8.125%	expense_custom_field.tax groups.11	2022-09-20 08:39:11.013446+00	2022-09-20 08:39:11.013525+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2671	TAX_GROUPS	Tax Groups	tax for usa @8.125%	expense_custom_field.tax groups.12	2022-09-20 08:39:11.013631+00	2022-09-20 08:39:11.013678+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2672	TAX_GROUPS	Tax Groups	tax for usass @8.125%	expense_custom_field.tax groups.13	2022-09-20 08:39:11.014332+00	2022-09-20 08:39:11.014452+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2673	TAX_GROUPS	Tax Groups	tax for ussr @8.125%	expense_custom_field.tax groups.14	2022-09-20 08:39:11.014851+00	2022-09-20 08:39:11.014906+00	1	\N	{"placeholder": "Select Tax Groups", "is_dependent": false, "custom_field_id": 195201}	f	f
2622	TEAM_2_POSTMAN	Team 2 Postman	Dukes Basketball Camp	expense_custom_field.team 2 postman.1	2022-09-20 08:39:10.992147+00	2022-09-20 08:39:10.992414+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2623	TEAM_2_POSTMAN	Team 2 Postman	Gevelber Photography	expense_custom_field.team 2 postman.2	2022-09-20 08:39:10.993352+00	2022-09-20 08:39:10.993408+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2624	TEAM_2_POSTMAN	Team 2 Postman	Geeta Kalapatapu	expense_custom_field.team 2 postman.3	2022-09-20 08:39:10.993564+00	2022-09-20 08:39:10.993635+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2625	TEAM_2_POSTMAN	Team 2 Postman	Bill's Windsurf Shop	expense_custom_field.team 2 postman.4	2022-09-20 08:39:10.993761+00	2022-09-20 08:39:10.993806+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2626	TEAM_2_POSTMAN	Team 2 Postman	Diego Rodriguez	expense_custom_field.team 2 postman.5	2022-09-20 08:39:10.993903+00	2022-09-20 08:39:10.993941+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2627	TEAM_2_POSTMAN	Team 2 Postman	Amy's Bird Sanctuary:Test Project	expense_custom_field.team 2 postman.6	2022-09-20 08:39:10.994057+00	2022-09-20 08:39:10.994101+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2628	TEAM_2_POSTMAN	Team 2 Postman	Dylan Sollfrank	expense_custom_field.team 2 postman.7	2022-09-20 08:39:10.994406+00	2022-09-20 08:39:10.994458+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2629	TEAM_2_POSTMAN	Team 2 Postman	Sravan BLR Customer	expense_custom_field.team 2 postman.8	2022-09-20 08:39:10.994547+00	2022-09-20 08:39:10.994577+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2630	TEAM_2_POSTMAN	Team 2 Postman	Kate Whelan	expense_custom_field.team 2 postman.9	2022-09-20 08:39:10.994662+00	2022-09-20 08:39:10.99471+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2631	TEAM_2_POSTMAN	Team 2 Postman	Coffee	expense_custom_field.team 2 postman.10	2022-09-20 08:39:10.994792+00	2022-09-20 08:39:10.994821+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2632	TEAM_2_POSTMAN	Team 2 Postman	Sushi by Katsuyuki	expense_custom_field.team 2 postman.11	2022-09-20 08:39:10.99489+00	2022-09-20 08:39:10.994919+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2633	TEAM_2_POSTMAN	Team 2 Postman	Freeman Sporting Goods:55 Twin Lane	expense_custom_field.team 2 postman.12	2022-09-20 08:39:10.99499+00	2022-09-20 08:39:10.995021+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2634	TEAM_2_POSTMAN	Team 2 Postman	Diego Rodriguez:Test Project	expense_custom_field.team 2 postman.13	2022-09-20 08:39:10.995543+00	2022-09-20 08:39:10.995585+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2635	TEAM_2_POSTMAN	Team 2 Postman	Chai	expense_custom_field.team 2 postman.14	2022-09-20 08:39:10.995665+00	2022-09-20 08:39:10.995692+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2636	TEAM_2_POSTMAN	Team 2 Postman	Cool Cars	expense_custom_field.team 2 postman.15	2022-09-20 08:39:10.995758+00	2022-09-20 08:39:10.995785+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2637	TEAM_2_POSTMAN	Team 2 Postman	Amy's Bird Sanctuary	expense_custom_field.team 2 postman.16	2022-09-20 08:39:10.99585+00	2022-09-20 08:39:10.995877+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2638	TEAM_2_POSTMAN	Team 2 Postman	Freeman Sporting Goods	expense_custom_field.team 2 postman.17	2022-09-20 08:39:10.995942+00	2022-09-20 08:39:10.995969+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2639	TEAM_2_POSTMAN	Team 2 Postman	Shara Barnett	expense_custom_field.team 2 postman.18	2022-09-20 08:39:10.996035+00	2022-09-20 08:39:10.996062+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2640	TEAM_2_POSTMAN	Team 2 Postman	Kookies by Kathy	expense_custom_field.team 2 postman.19	2022-09-20 08:39:10.996126+00	2022-09-20 08:39:10.996153+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2641	TEAM_2_POSTMAN	Team 2 Postman	Jeff's Jalopies	expense_custom_field.team 2 postman.20	2022-09-20 08:39:10.996217+00	2022-09-20 08:39:10.996244+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2642	TEAM_2_POSTMAN	Team 2 Postman	Red Rock Diner	expense_custom_field.team 2 postman.21	2022-09-20 08:39:10.996309+00	2022-09-20 08:39:10.996336+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2643	TEAM_2_POSTMAN	Team 2 Postman	Wedding Planning by Whitney	expense_custom_field.team 2 postman.22	2022-09-20 08:39:10.996537+00	2022-09-20 08:39:10.996566+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2644	TEAM_2_POSTMAN	Team 2 Postman	Sonnenschein Family Store	expense_custom_field.team 2 postman.23	2022-09-20 08:39:10.996631+00	2022-09-20 08:39:10.996658+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2645	TEAM_2_POSTMAN	Team 2 Postman	Shara Barnett:Barnett Design	expense_custom_field.team 2 postman.24	2022-09-20 08:39:10.996722+00	2022-09-20 08:39:10.99675+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2646	TEAM_2_POSTMAN	Team 2 Postman	Travis Waldron	expense_custom_field.team 2 postman.25	2022-09-20 08:39:10.996815+00	2022-09-20 08:39:10.996842+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2647	TEAM_2_POSTMAN	Team 2 Postman	Rondonuwu Fruit and Vegi	expense_custom_field.team 2 postman.26	2022-09-20 08:39:10.996907+00	2022-09-20 08:39:10.996934+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2648	TEAM_2_POSTMAN	Team 2 Postman	Ashwinn	expense_custom_field.team 2 postman.27	2022-09-20 08:39:10.996999+00	2022-09-20 08:39:10.997026+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2649	TEAM_2_POSTMAN	Team 2 Postman	Paulsen Medical Supplies	expense_custom_field.team 2 postman.28	2022-09-20 08:39:10.997091+00	2022-09-20 08:39:10.997118+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2650	TEAM_2_POSTMAN	Team 2 Postman	wraith squad	expense_custom_field.team 2 postman.29	2022-09-20 08:39:10.997183+00	2022-09-20 08:39:10.99721+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2651	TEAM_2_POSTMAN	Team 2 Postman	Weiskopf Consulting	expense_custom_field.team 2 postman.30	2022-09-20 08:39:10.997275+00	2022-09-20 08:39:10.997302+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2652	TEAM_2_POSTMAN	Team 2 Postman	octane squad	expense_custom_field.team 2 postman.31	2022-09-20 08:39:10.997483+00	2022-09-20 08:39:10.997513+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2653	TEAM_2_POSTMAN	Team 2 Postman	naruto uzumaki	expense_custom_field.team 2 postman.32	2022-09-20 08:39:10.997589+00	2022-09-20 08:39:10.997616+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2654	TEAM_2_POSTMAN	Team 2 Postman	Rago Travel Agency	expense_custom_field.team 2 postman.33	2022-09-20 08:39:10.997681+00	2022-09-20 08:39:10.997708+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2655	TEAM_2_POSTMAN	Team 2 Postman	Mark Cho	expense_custom_field.team 2 postman.34	2022-09-20 08:39:10.997773+00	2022-09-20 08:39:10.9978+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2656	TEAM_2_POSTMAN	Team 2 Postman	Freeman Sporting Goods:0969 Ocean View Road	expense_custom_field.team 2 postman.35	2022-09-20 08:39:10.997865+00	2022-09-20 08:39:10.997892+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2657	TEAM_2_POSTMAN	Team 2 Postman	Pye's Cakes	expense_custom_field.team 2 postman.36	2022-09-20 08:39:10.997957+00	2022-09-20 08:39:10.998009+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2658	TEAM_2_POSTMAN	Team 2 Postman	John Melton	expense_custom_field.team 2 postman.37	2022-09-20 08:39:10.998079+00	2022-09-20 08:39:10.998108+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
2659	TEAM_2_POSTMAN	Team 2 Postman	Video Games by Dan	expense_custom_field.team 2 postman.38	2022-09-20 08:39:10.998183+00	2022-09-20 08:39:10.998211+00	1	\N	{"placeholder": "Select Team 2 Postman", "is_dependent": true, "custom_field_id": 174994}	f	f
\.


--
-- Data for Name: expense_attributes_deletion_cache; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_attributes_deletion_cache (id, category_ids, project_ids, workspace_id, cost_center_ids, custom_field_list, merchant_list, updated_at) FROM stdin;
\.


--
-- Data for Name: expense_fields; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_fields (id, attribute_type, source_field_id, is_enabled, created_at, updated_at, workspace_id) FROM stdin;
\.


--
-- Data for Name: expense_filters; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_filters (id, condition, operator, "values", rank, join_by, is_custom, custom_field_type, created_at, updated_at, workspace_id) FROM stdin;
\.


--
-- Data for Name: expense_group_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_group_settings (id, reimbursable_expense_group_fields, corporate_credit_card_expense_group_fields, expense_state, reimbursable_export_date_type, created_at, updated_at, workspace_id, ccc_export_date_type, ccc_expense_state, split_expense_grouping, created_by, updated_by) FROM stdin;
1	{employee_email,report_id,claim_number,fund_source}	{employee_email,report_id,expense_id,claim_number,fund_source}	PAYMENT_PROCESSING	current_date	2022-09-20 08:38:03.358472+00	2022-09-20 08:39:32.022875+00	1	spent_at	PAID	MULTIPLE_LINE_ITEM	\N	\N
\.


--
-- Data for Name: expense_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_groups (id, description, created_at, updated_at, workspace_id, fund_source, exported_at, export_type, employee_name, response_logs, export_url) FROM stdin;
1	{"report_id": "rpEZGqVCyWxQ", "fund_source": "PERSONAL", "claim_number": "C/2022/09/R/21", "employee_email": "ashwin.t@fyle.in"}	2022-09-20 08:48:21.765399+00	2022-09-20 08:48:21.765445+00	1	PERSONAL	\N	\N	\N	\N	\N
2	{"report_id": "rpSTYO8AfUVA", "expense_id": "txCqLqsEnAjf", "fund_source": "CCC", "claim_number": "C/2022/09/R/22", "employee_email": "ashwin.t@fyle.in"}	2022-09-20 08:51:27.651115+00	2022-09-20 08:51:27.651167+00	1	CCC	\N	\N	\N	\N	\N
3	{"report_id": "rpBf5ibqUT6B", "expense_id": "txTHfEPWOEOp", "fund_source": "CCC", "claim_number": "C/2022/09/R/23", "employee_email": "ashwin.t@fyle.in"}	2022-09-20 08:56:50.147276+00	2022-09-20 08:56:50.147324+00	1	CCC	\N	\N	\N	\N	\N
\.


--
-- Data for Name: expense_groups_expenses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_groups_expenses (id, expensegroup_id, expense_id) FROM stdin;
1	1	1
2	2	2
3	3	3
\.


--
-- Data for Name: expense_report_lineitems; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_report_lineitems (id, expense_type_id, gl_account_number, project_id, location_id, department_id, memo, amount, created_at, updated_at, expense_report_id, expense_id, transaction_date, billable, customer_id, item_id, user_defined_dimensions, expense_payment_type, class_id, tax_amount, tax_code, cost_type_id, task_id, vendor_id) FROM stdin;
\.


--
-- Data for Name: expense_reports; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expense_reports (id, employee_id, description, supdoc_id, created_at, updated_at, expense_group_id, memo, transaction_date, paid_on_sage_intacct, payment_synced, currency, is_retired) FROM stdin;
\.


--
-- Data for Name: expenses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expenses (id, employee_email, category, sub_category, project, expense_id, expense_number, claim_number, amount, currency, foreign_amount, foreign_currency, settlement_id, reimbursable, state, vendor, cost_center, purpose, report_id, spent_at, approved_at, expense_created_at, expense_updated_at, created_at, updated_at, fund_source, custom_properties, verified_at, billable, paid_on_sage_intacct, org_id, tax_amount, tax_group_id, file_ids, payment_number, corporate_card_id, is_skipped, report_title, posted_at, employee_name, accounting_export_summary, previous_export_state, workspace_id, paid_on_fyle, bank_transaction_id, is_posted_at_null, masked_corporate_card_number, imported_from) FROM stdin;
1	ashwin.t@fyle.in	Food	\N	Aaron Abbott	txR9dyrqr1Jn	E/2022/09/T/21	C/2022/09/R/21	21	USD	\N	\N	setqwcKcC9q1k	t	PAYMENT_PROCESSING	Ashwin	Marketing	\N	rpEZGqVCyWxQ	2022-09-20 17:00:00+00	2022-09-19 19:54:36.96+00	2022-09-19 19:54:15.870239+00	2022-09-19 19:55:58.641995+00	2022-09-20 08:48:21.737374+00	2022-09-20 08:48:21.737392+00	PERSONAL	{"Team": "", "Class": "", "Klass": "", "Location": "", "Team Copy": "", "Tax Groups": "", "Departments": "", "Team 2 Postman": "", "User Dimension": "", "Location Entity": "", "Operating System": "", "System Operating": "", "User Dimension Copy": "", "Custom Expense Field": null}	\N	\N	f	or79Cob97KSh	\N	\N	{}	P/2022/09/R/18	\N	f	\N	\N	\N	{}	\N	\N	f	\N	f	\N	\N
2	ashwin.t@fyle.in	Food	\N	Aaron Abbott	txCqLqsEnAjf	E/2022/09/T/22	C/2022/09/R/22	11	USD	\N	\N	setzhjuqQ6Pl5	f	PAYMENT_PROCESSING	Ashwin	Marketing	\N	rpSTYO8AfUVA	2022-09-20 17:00:00+00	2022-09-20 08:50:48.428+00	2022-09-20 08:50:27.570399+00	2022-09-20 08:51:13.891379+00	2022-09-20 08:51:27.566571+00	2022-09-20 08:51:27.566598+00	CCC	{"Team": "", "Class": "", "Klass": "", "Location": "", "Team Copy": "", "Tax Groups": "", "Departments": "", "Team 2 Postman": "", "User Dimension": "", "Location Entity": "", "Operating System": "", "System Operating": "", "User Dimension Copy": "", "Custom Expense Field": null}	\N	t	f	or79Cob97KSh	2.41	tggu76WXIdjY	{}	P/2022/09/R/19	\N	f	\N	\N	\N	{}	\N	\N	f	\N	f	\N	\N
3	ashwin.t@fyle.in	Taxi	\N	Aaron Abbott	txTHfEPWOEOp	E/2022/09/T/23	C/2022/09/R/23	22	USD	\N	\N	set0SnAq66Zbq	f	PAYMENT_PROCESSING	Ashwin	Marketing	\N	rpBf5ibqUT6B	2022-09-20 17:00:00+00	2022-09-20 08:56:09.337+00	2022-09-20 08:55:53.246893+00	2022-09-20 08:56:40.795304+00	2022-09-20 08:56:50.117313+00	2022-09-20 08:56:50.117349+00	CCC	{"Team": "", "Class": "", "Klass": "", "Location": "", "Team Copy": "", "Tax Groups": "", "Departments": "", "Team 2 Postman": "", "User Dimension": "", "Location Entity": "", "Operating System": "", "System Operating": "", "User Dimension Copy": "", "Custom Expense Field": null}	\N	\N	f	or79Cob97KSh	4.81	tggu76WXIdjY	{}	P/2022/09/R/20	\N	f	\N	\N	\N	{}	\N	\N	f	\N	f	\N	\N
\.


--
-- Data for Name: failed_events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.failed_events (id, routing_key, payload, created_at, updated_at, error_traceback, workspace_id, is_resolved) FROM stdin;
\.


--
-- Data for Name: feature_configs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.feature_configs (id, export_via_rabbitmq, created_at, updated_at, workspace_id, import_via_rabbitmq, fyle_webhook_sync_enabled, migrated_to_rest_api) FROM stdin;
1	f	2025-10-10 09:38:10.289737+00	2025-10-10 09:38:10.289737+00	1	f	t	f
\.


--
-- Data for Name: fyle_credentials; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fyle_credentials (id, refresh_token, created_at, updated_at, workspace_id, cluster_domain) FROM stdin;
1	eyJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2NjM2NjMwNzIsImlzcyI6IkZ5bGVBcHAiLCJvcmdfdXNlcl9pZCI6Ilwib3VWTE9ZUDhsZWxOXCIiLCJ0cGFfaWQiOiJcInRwYXlmalBQSFREZ3ZcIiIsInRwYV9uYW1lIjoiXCJGeWxlIDw-IFNhZ2UgSW4uLlwiIiwiY2x1c3Rlcl9kb21haW4iOiJcImh0dHBzOi8vc3RhZ2luZy5meWxlLnRlY2hcIiIsImV4cCI6MTk3OTAyMzA3Mn0.NGRySUzDx7ycSD_6LaRy_wTGMD7Yl-u3I1FmOo9BWhk	2022-09-20 08:38:03.43928+00	2022-09-20 08:38:03.439323+00	1	https://staging.fyle.tech
\.


--
-- Data for Name: fyle_sync_timestamps; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fyle_sync_timestamps (id, category_synced_at, project_synced_at, cost_center_synced_at, employee_synced_at, expense_field_synced_at, corporate_card_synced_at, dependent_field_synced_at, tax_group_synced_at, created_at, updated_at, workspace_id) FROM stdin;
1	\N	\N	\N	\N	\N	\N	\N	\N	2025-10-31 06:45:42.644775+00	2025-10-31 06:45:42.644775+00	1
\.


--
-- Data for Name: general_mappings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.general_mappings (id, default_location_name, default_location_id, default_department_name, default_department_id, default_project_name, default_project_id, created_at, updated_at, workspace_id, default_charge_card_name, default_charge_card_id, default_ccc_vendor_name, default_ccc_vendor_id, default_item_id, default_item_name, payment_account_id, payment_account_name, default_ccc_expense_payment_type_id, default_ccc_expense_payment_type_name, default_reimbursable_expense_payment_type_id, default_reimbursable_expense_payment_type_name, use_intacct_employee_departments, use_intacct_employee_locations, location_entity_id, location_entity_name, default_class_id, default_class_name, default_tax_code_id, default_tax_code_name, default_credit_card_id, default_credit_card_name, default_gl_account_id, default_gl_account_name, created_by, updated_by) FROM stdin;
1	Australia	600	Admin	300	Branding Analysis	10061	2022-09-20 08:47:19.634467+00	2022-10-10 08:25:16.32686+00	1		20600		20043	1012	Cube	400_CHK	Demo Bank - 400_CHK		\N			f	f			600	Enterprise	W4 Withholding Tax	W4 Withholding Tax	20610	Accr. Sales Tax Payable	\N	\N	\N	\N
\.


--
-- Data for Name: import_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.import_logs (id, attribute_type, status, error_log, total_batches_count, processed_batches_count, last_successful_run_at, created_at, updated_at, workspace_id) FROM stdin;
\.


--
-- Data for Name: intacct_sync_timestamps; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.intacct_sync_timestamps (id, account_synced_at, vendor_synced_at, customer_synced_at, class_synced_at, employee_synced_at, item_synced_at, location_synced_at, allocation_synced_at, tax_detail_synced_at, department_synced_at, project_synced_at, expense_type_synced_at, location_entity_synced_at, payment_account_synced_at, expense_payment_type_synced_at, created_at, updated_at, workspace_id) FROM stdin;
1	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2025-11-21 18:32:09.962351+00	2025-11-21 18:32:09.962351+00	1
\.


--
-- Data for Name: journal_entries; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.journal_entries (id, description, memo, currency, supdoc_id, transaction_date, created_at, updated_at, expense_group_id) FROM stdin;
\.


--
-- Data for Name: journal_entry_lineitems; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.journal_entry_lineitems (id, gl_account_number, project_id, location_id, class_id, department_id, customer_id, item_id, memo, user_defined_dimensions, amount, billable, transaction_date, created_at, updated_at, expense_id, journal_entry_id, employee_id, vendor_id, tax_amount, tax_code, cost_type_id, task_id, allocation_id) FROM stdin;
\.


--
-- Data for Name: last_export_details; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.last_export_details (id, last_exported_at, export_mode, total_expense_groups_count, successful_expense_groups_count, failed_expense_groups_count, created_at, updated_at, workspace_id, next_export_at, unmapped_card_count) FROM stdin;
5	2023-07-08 09:30:15.56789+00	MANUAL	5	4	1	2023-07-08 09:30:15.56789+00	2023-07-08 09:30:15.56789+00	1	2023-07-09 09:30:15.56789+00	0
\.


--
-- Data for Name: location_entity_mappings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.location_entity_mappings (id, location_entity_name, country_name, destination_id, created_at, updated_at, workspace_id) FROM stdin;
1	Australia	Australia	600	2022-09-20 08:39:00.668977+00	2022-09-20 08:39:00.669049+00	1
\.


--
-- Data for Name: mapping_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mapping_settings (id, source_field, destination_field, created_at, updated_at, workspace_id, import_to_fyle, is_custom, source_placeholder, expense_field_id, created_by, updated_by) FROM stdin;
1	EMPLOYEE	EMPLOYEE	2022-09-20 08:39:32.083277+00	2022-09-20 08:39:32.083321+00	1	f	f	\N	\N	\N	\N
2	CATEGORY	EXPENSE_TYPE	2022-09-20 08:39:32.159859+00	2022-09-20 08:39:32.159909+00	1	f	f	\N	\N	\N	\N
4	EMPLOYEE	VENDOR	2022-09-20 08:46:24.843685+00	2022-09-20 08:46:24.843742+00	1	f	f	\N	\N	\N	\N
5	CATEGORY	ACCOUNT	2022-09-20 08:46:24.937151+00	2022-09-20 08:46:24.937198+00	1	f	f	\N	\N	\N	\N
3	PROJECT	PROJECT	2022-09-20 08:39:32.268681+00	2022-09-20 08:46:24.988239+00	1	t	f	\N	\N	\N	\N
666	TAX_GROUP	TAX_CODE	2022-09-20 08:39:32.268681+00	2022-09-20 08:46:24.988239+00	1	t	f	\N	\N	\N	\N
\.


--
-- Data for Name: mappings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mappings (id, source_type, destination_type, created_at, updated_at, destination_id, source_id, workspace_id) FROM stdin;
1	PROJECT	PROJECT	2022-09-20 08:40:25.866372+00	2022-09-20 08:40:25.866416+00	602	3218	1
2	PROJECT	PROJECT	2022-09-20 08:40:25.866474+00	2022-09-20 08:40:25.866504+00	599	3219	1
3	PROJECT	PROJECT	2022-09-20 08:40:25.866558+00	2022-09-20 08:40:25.866587+00	598	3220	1
4	PROJECT	PROJECT	2022-09-20 08:40:25.866639+00	2022-09-20 08:40:25.866668+00	601	3221	1
5	PROJECT	PROJECT	2022-09-20 08:40:25.866721+00	2022-09-20 08:40:25.86675+00	609	1860	1
6	PROJECT	PROJECT	2022-09-20 08:40:25.866801+00	2022-09-20 08:40:25.86683+00	612	688	1
7	PROJECT	PROJECT	2022-09-20 08:40:25.866881+00	2022-09-20 08:40:25.86691+00	605	1861	1
8	PROJECT	PROJECT	2022-09-20 08:40:25.866961+00	2022-09-20 08:40:25.86699+00	606	1862	1
9	PROJECT	PROJECT	2022-09-20 08:40:25.867042+00	2022-09-20 08:40:25.867071+00	610	1863	1
10	PROJECT	PROJECT	2022-09-20 08:40:25.867122+00	2022-09-20 08:40:25.868347+00	611	1864	1
11	PROJECT	PROJECT	2022-09-20 08:40:25.869298+00	2022-09-20 08:40:25.869483+00	613	1865	1
12	PROJECT	PROJECT	2022-09-20 08:40:25.872684+00	2022-09-20 08:40:25.873014+00	600	1870	1
13	PROJECT	PROJECT	2022-09-20 08:40:25.873601+00	2022-09-20 08:40:25.873804+00	603	1866	1
14	PROJECT	PROJECT	2022-09-20 08:40:25.874137+00	2022-09-20 08:40:25.87417+00	604	1867	1
15	PROJECT	PROJECT	2022-09-20 08:40:25.874787+00	2022-09-20 08:40:25.874823+00	607	1868	1
16	PROJECT	PROJECT	2022-09-20 08:40:25.874882+00	2022-09-20 08:40:25.874912+00	608	1869	1
160	PROJECT	CUSTOMER	2022-09-20 08:40:25.874882+00	2022-09-20 08:40:25.874912+00	614	1	1
17	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.625158+00	2022-09-29 12:09:34.625202+00	589	3233	1
18	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.625256+00	2022-09-29 12:09:34.625286+00	583	3229	1
19	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.625338+00	2022-09-29 12:09:34.625368+00	594	3246	1
20	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.62542+00	2022-09-29 12:09:34.625449+00	593	2939	1
21	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.625501+00	2022-09-29 12:09:34.62553+00	559	3230	1
22	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.625582+00	2022-09-29 12:09:34.625612+00	560	2884	1
23	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.625663+00	2022-09-29 12:09:34.625693+00	561	2692	1
24	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.625745+00	2022-09-29 12:09:34.625774+00	562	3252	1
25	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.625826+00	2022-09-29 12:09:34.625855+00	563	3254	1
26	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.625907+00	2022-09-29 12:09:34.625936+00	564	2725	1
27	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.62752+00	2022-09-29 12:09:34.628546+00	565	2968	1
28	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.628792+00	2022-09-29 12:09:34.629404+00	566	3250	1
29	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.630356+00	2022-09-29 12:09:34.630412+00	579	2869	1
30	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.631269+00	2022-09-29 12:09:34.631309+00	584	3041	1
31	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.634545+00	2022-09-29 12:09:34.634583+00	585	2922	1
32	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.634639+00	2022-09-29 12:09:34.634668+00	575	2875	1
33	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.634721+00	2022-09-29 12:09:34.63475+00	576	3232	1
34	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.634803+00	2022-09-29 12:09:34.634832+00	582	3234	1
35	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.635751+00	2022-09-29 12:09:34.636281+00	581	2834	1
36	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.636474+00	2022-09-29 12:09:34.636518+00	580	3237	1
37	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.63658+00	2022-09-29 12:09:34.63661+00	586	3235	1
38	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.636662+00	2022-09-29 12:09:34.636692+00	577	2840	1
39	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.636744+00	2022-09-29 12:09:34.636773+00	578	3241	1
40	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.636826+00	2022-09-29 12:09:34.636855+00	588	3228	1
41	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.636907+00	2022-09-29 12:09:34.637467+00	587	2954	1
42	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.63805+00	2022-09-29 12:09:34.638087+00	574	3251	1
43	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.639538+00	2022-09-29 12:09:34.639569+00	597	3248	1
44	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.639745+00	2022-09-29 12:09:34.639776+00	595	3236	1
45	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.639934+00	2022-09-29 12:09:34.639964+00	596	2751	1
46	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.640017+00	2022-09-29 12:09:34.640046+00	592	2822	1
47	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.640098+00	2022-09-29 12:09:34.640127+00	591	2857	1
48	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.640179+00	2022-09-29 12:09:34.640208+00	567	3238	1
49	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.64026+00	2022-09-29 12:09:34.640289+00	568	2984	1
50	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.640341+00	2022-09-29 12:09:34.64037+00	569	2737	1
51	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.640422+00	2022-09-29 12:09:34.640451+00	570	3247	1
52	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.640503+00	2022-09-29 12:09:34.640532+00	571	3253	1
53	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.640584+00	2022-09-29 12:09:34.640613+00	572	2905	1
54	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.640665+00	2022-09-29 12:09:34.640694+00	573	2947	1
55	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.640746+00	2022-09-29 12:09:34.640775+00	544	3242	1
56	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.640827+00	2022-09-29 12:09:34.640856+00	545	3243	1
57	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.640908+00	2022-09-29 12:09:34.640937+00	546	2720	1
58	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.640989+00	2022-09-29 12:09:34.641199+00	547	2916	1
59	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.641253+00	2022-09-29 12:09:34.641282+00	548	3249	1
60	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.641334+00	2022-09-29 12:09:34.641364+00	549	3245	1
61	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.641415+00	2022-09-29 12:09:34.641444+00	550	2873	1
62	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.641496+00	2022-09-29 12:09:34.641525+00	551	3019	1
63	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.641577+00	2022-09-29 12:09:34.641607+00	552	3240	1
64	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.641659+00	2022-09-29 12:09:34.641702+00	553	2982	1
65	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.641755+00	2022-09-29 12:09:34.641784+00	554	2893	1
66	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.641836+00	2022-09-29 12:09:34.641865+00	555	3239	1
67	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.699518+00	2022-09-29 12:09:34.699563+00	556	2747	1
68	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.699623+00	2022-09-29 12:09:34.699655+00	557	2909	1
69	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.69971+00	2022-09-29 12:09:34.699741+00	558	3231	1
70	TAX_GROUP	TAX_DETAIL	2022-09-29 12:09:34.699794+00	2022-09-29 12:09:34.699824+00	590	3244	1
\.


--
-- Data for Name: reimbursements; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reimbursements (id, settlement_id, reimbursement_id, state, created_at, updated_at, workspace_id, payment_number) FROM stdin;
1	setqwcKcC9q1k	reimzte4XjS5tx	PENDING	2022-09-20 08:47:51.808108+00	2022-09-20 08:47:51.808176+00	1	P/2022/09/R/18
2	set5FLB0eh8xU	reim2RjmQmJsUD	COMPLETE	2022-09-20 08:47:51.808248+00	2022-09-20 08:47:51.808281+00	1	P/2022/05/R/11
3	setjlrzx3KsTr	reim5Ig0uFpbo3	COMPLETE	2022-09-20 08:47:51.808422+00	2022-09-20 08:47:51.808453+00	1	P/2022/06/R/17
4	setmOIibblGoO	reime84IEu8wnG	COMPLETE	2022-09-20 08:47:51.808505+00	2022-09-20 08:47:51.808535+00	1	P/2022/06/R/15
5	setiy4J9cu4lV	reimeEcHpUxZ1L	COMPLETE	2022-09-20 08:47:51.808585+00	2022-09-20 08:47:51.808614+00	1	P/2022/06/R/11
6	set3llK6jy981	reimFd2WUwdrbJ	COMPLETE	2022-09-20 08:47:51.808664+00	2022-09-20 08:47:51.808693+00	1	P/2022/06/R/16
7	setMFIF5t1xZM	reimh6EMg30WNY	COMPLETE	2022-09-20 08:47:51.808734+00	2022-09-20 08:47:51.808763+00	1	P/2022/06/R/5
8	setvJYD03y62Z	reimHpPPfefahf	COMPLETE	2022-09-20 08:47:51.812682+00	2022-09-20 08:47:51.812739+00	1	P/2022/06/R/8
9	setxlydfOSEml	reimidjcT51i27	COMPLETE	2022-09-20 08:47:51.812808+00	2022-09-20 08:47:51.812842+00	1	P/2022/06/R/12
10	set70JEvCZqpM	reimKj2P1QF8ie	COMPLETE	2022-09-20 08:47:51.812899+00	2022-09-20 08:47:51.81293+00	1	P/2022/06/R/10
11	setrElGUl12ZH	reimlomI5EMKMh	COMPLETE	2022-09-20 08:47:51.812975+00	2022-09-20 08:47:51.812996+00	1	P/2022/06/R/6
12	setUXsf02fMoD	reimmgo2w4kva6	COMPLETE	2022-09-20 08:47:51.813046+00	2022-09-20 08:47:51.813057+00	1	P/2022/06/R/7
13	setzNuDqnpKlJ	reimPHrm7mFOXo	COMPLETE	2022-09-20 08:47:51.813096+00	2022-09-20 08:47:51.813125+00	1	P/2022/06/R/4
14	set2sqoTh6wb0	reimrHkkHUJ8Gn	COMPLETE	2022-09-20 08:47:51.81318+00	2022-09-20 08:47:51.813227+00	1	P/2022/05/R/14
15	setZUJiexagYV	reimTQIdCC1cxh	COMPLETE	2022-09-20 08:47:51.813677+00	2022-09-20 08:47:51.81371+00	1	P/2022/06/R/13
16	setp8l6eBKsMq	reimvpdXPsWWhu	COMPLETE	2022-09-20 08:47:51.813761+00	2022-09-20 08:47:51.81378+00	1	P/2022/06/R/3
17	set3j7OPg6Yl5	reimVUTPgEBWij	COMPLETE	2022-09-20 08:47:51.813818+00	2022-09-20 08:47:51.813847+00	1	P/2022/06/R/9
18	set8gJFi2HOmA	reimxHWDq39irq	COMPLETE	2022-09-20 08:47:51.813898+00	2022-09-20 08:47:51.813925+00	1	P/2022/06/R/2
19	setmOppa5zapS	reimXMxDsWHuXs	COMPLETE	2022-09-20 08:47:51.813965+00	2022-09-20 08:47:51.813986+00	1	P/2022/06/R/14
20	setj5Pk3oxJlx	reimyzPqNZtctG	COMPLETE	2022-09-20 08:47:51.814029+00	2022-09-20 08:47:51.814049+00	1	P/2022/05/R/12
21	setswbV0CUUFX	reimz57kBsJtld	COMPLETE	2022-09-20 08:47:51.814094+00	2022-09-20 08:47:51.814115+00	1	P/2022/05/R/13
22	setWkgMfopVep	reim0nbuTxhdkO	COMPLETE	2022-09-20 08:47:51.814163+00	2022-09-20 08:47:51.814192+00	1	P/2022/08/R/9
23	set2PSQwMhM6U	reim0YeymLba9C	COMPLETE	2022-09-20 08:47:51.814241+00	2022-09-20 08:47:51.81427+00	1	P/2022/08/R/5
24	setXt57nb6pKe	reim5ukhDLAnTq	COMPLETE	2022-09-20 08:47:51.814318+00	2022-09-20 08:47:51.814483+00	1	P/2022/08/R/17
25	setkPoEupZuYN	reimDkBxBu4yZf	COMPLETE	2022-09-20 08:47:51.814533+00	2022-09-20 08:47:51.814572+00	1	P/2022/08/R/18
26	setAeXPftpTJs	reimDNiCqHYHgS	COMPLETE	2022-09-20 08:47:51.814854+00	2022-09-20 08:47:51.814883+00	1	P/2022/08/R/7
27	set8a1tCmnYFS	reimetc9gMzjbc	COMPLETE	2022-09-20 08:47:51.814933+00	2022-09-20 08:47:51.814962+00	1	P/2022/08/R/11
28	setWz9XHlAq0A	reimGcNnYhpdIM	COMPLETE	2022-09-20 08:47:51.815011+00	2022-09-20 08:47:51.81504+00	1	P/2022/08/R/4
29	setgknnFFrKZm	reimGGoOlCtQxK	COMPLETE	2022-09-20 08:47:51.815088+00	2022-09-20 08:47:51.815117+00	1	P/2022/08/R/12
30	setvBgVgJrdp7	reimHg1m3UfObg	COMPLETE	2022-09-20 08:47:51.815166+00	2022-09-20 08:47:51.815188+00	1	P/2022/08/R/16
31	setEk25Ej2dYa	reimjggxQT2KT2	COMPLETE	2022-09-20 08:47:51.815227+00	2022-09-20 08:47:51.815253+00	1	P/2022/08/R/19
32	setV33iekWALa	reimKJxRnxnBJS	COMPLETE	2022-09-20 08:47:51.815295+00	2022-09-20 08:47:51.815316+00	1	P/2022/08/R/1
33	settgdQdi3kHO	reimKXsoQHd92z	COMPLETE	2022-09-20 08:47:51.815482+00	2022-09-20 08:47:51.815511+00	1	P/2022/08/R/6
34	setRMWuk4iYw9	reimnmvK7cV55S	COMPLETE	2022-09-20 08:47:51.81556+00	2022-09-20 08:47:51.815585+00	1	P/2022/08/R/14
35	setTtUB3Nxv64	reimP6VNLbE30x	COMPLETE	2022-09-20 08:47:51.81562+00	2022-09-20 08:47:51.81564+00	1	P/2022/08/R/13
36	setPg0GGgvKQI	reimP6x08mtt8I	COMPLETE	2022-09-20 08:47:51.815688+00	2022-09-20 08:47:51.815711+00	1	P/2022/08/R/15
37	setwE5XebQxQ7	reimS4CRRgYoRW	COMPLETE	2022-09-20 08:47:51.815749+00	2022-09-20 08:47:51.815762+00	1	P/2022/08/R/10
38	set76k4HcGUtW	reimu81hqajeUC	COMPLETE	2022-09-20 08:47:51.815799+00	2022-09-20 08:47:51.815828+00	1	P/2022/08/R/3
39	setFqwEHTJjrK	reimUTW9JYjtHU	COMPLETE	2022-09-20 08:47:51.815894+00	2022-09-20 08:47:51.816099+00	1	P/2022/08/R/8
40	setwUhRA0KaY4	reimX2Ixjiz7Vz	COMPLETE	2022-09-20 08:47:51.816147+00	2022-09-20 08:47:51.816163+00	1	P/2022/07/R/1
41	setUYgcGYmtmG	reimXluEZX1lnI	COMPLETE	2022-09-20 08:47:51.816193+00	2022-09-20 08:47:51.816204+00	1	P/2022/08/R/2
42	setiky8BvnZe2	reim1HUbZT2Uwb	COMPLETE	2022-09-20 08:47:51.816344+00	2022-09-20 08:47:51.816374+00	1	P/2022/09/R/5
43	setuA9bmHMCAB	reim7BEPKbVShk	COMPLETE	2022-09-20 08:47:51.816417+00	2022-09-20 08:47:51.816438+00	1	P/2022/09/R/12
44	setbLjsy1xfjA	reim9cHfXO85I8	COMPLETE	2022-09-20 08:47:51.816486+00	2022-09-20 08:47:51.816515+00	1	P/2022/08/R/24
45	setwxULQx5tq2	reimA8qgYTWcWH	COMPLETE	2022-09-20 08:47:51.816563+00	2022-09-20 08:47:51.816592+00	1	P/2022/09/R/11
46	setkpwnVyO3y5	reimEhgLUezlly	COMPLETE	2022-09-20 08:47:51.81664+00	2022-09-20 08:47:51.816668+00	1	P/2022/09/R/4
47	set1ajeVe3WRn	reimFntqayhgSZ	COMPLETE	2022-09-20 08:47:51.816716+00	2022-09-20 08:47:51.816744+00	1	P/2022/09/R/9
48	setNr2gpPnW5d	reimGu7DSy6msg	COMPLETE	2022-09-20 08:47:51.816793+00	2022-09-20 08:47:51.816821+00	1	P/2022/09/R/13
49	setM00XOyYg1I	reimHGvrzP8ssT	COMPLETE	2022-09-20 08:47:51.816869+00	2022-09-20 08:47:51.816898+00	1	P/2022/09/R/10
50	setlqphxXzMTJ	reimhZuvy914g5	COMPLETE	2022-09-20 08:47:51.816946+00	2022-09-20 08:47:51.816975+00	1	P/2022/09/R/6
51	setJ5iHytj8dq	reimJhGrnPNrnX	COMPLETE	2022-09-20 08:47:51.822402+00	2022-09-20 08:47:51.82245+00	1	P/2022/09/R/15
52	setkUxPBznLvB	reimP2ybXzvgpi	COMPLETE	2022-09-20 08:47:51.822581+00	2022-09-20 08:47:51.822614+00	1	P/2022/08/R/20
53	setHhVs7ch1f3	reimrRSByPXrfN	COMPLETE	2022-09-20 08:47:51.82267+00	2022-09-20 08:47:51.822701+00	1	P/2022/09/R/14
54	setbeE1A4FsJU	reims6JCiLNxFH	COMPLETE	2022-09-20 08:47:51.822754+00	2022-09-20 08:47:51.822784+00	1	P/2022/09/R/1
55	setanvdyKD6dO	reimSqj0iAonFo	COMPLETE	2022-09-20 08:47:51.822835+00	2022-09-20 08:47:51.822865+00	1	P/2022/09/R/7
56	sethxBoyUzcz6	reimUJs0SdG6dL	COMPLETE	2022-09-20 08:47:51.822914+00	2022-09-20 08:47:51.822936+00	1	P/2022/08/R/23
57	setA8r2MzF3kK	reimUzDJ5dUjkf	COMPLETE	2022-09-20 08:47:51.823341+00	2022-09-20 08:47:51.823392+00	1	P/2022/09/R/8
58	setuTsN3SkzH6	reimvck3fBDKrf	COMPLETE	2022-09-20 08:47:51.823454+00	2022-09-20 08:47:51.823476+00	1	P/2022/08/R/21
59	setnT6AjMPLB0	reimvPNgRCXhkc	COMPLETE	2022-09-20 08:47:51.823528+00	2022-09-20 08:47:51.823558+00	1	P/2022/09/R/2
60	setld9H2KG04t	reimWFb1v6hoe2	COMPLETE	2022-09-20 08:47:51.823609+00	2022-09-20 08:47:51.823638+00	1	P/2022/09/R/3
61	setwrURFfkW7c	reimWI4cDyd1r6	COMPLETE	2022-09-20 08:47:51.823688+00	2022-09-20 08:47:51.823717+00	1	P/2022/08/R/22
62	setWf2v1zXLMZ	reimcjxGshI8hJ	COMPLETE	2022-09-20 08:47:51.823766+00	2022-09-20 08:47:51.823795+00	1	P/2022/09/R/16
63	setKV0ZDxp4TS	reimgjdi6u2Zf5	COMPLETE	2022-09-20 08:47:51.823844+00	2022-09-20 08:47:51.823873+00	1	P/2022/09/R/17
64	setikmPeawoBZ	reimFavFEXjoSv	COMPLETE	2022-09-20 08:47:51.823921+00	2022-09-20 08:47:51.823951+00	1	P/2022/07/R/2
65	setqmieWjVpZm	reimzaZeihks67	COMPLETE	2022-09-20 08:47:51.823999+00	2022-09-20 08:47:51.824028+00	1	P/2022/06/R/1
66	setGtUuWv5015	reim8Lk8pWGDWL	COMPLETE	2022-09-20 08:47:51.824076+00	2022-09-20 08:47:51.824105+00	1	P/2022/05/R/6
67	set9k3fC23ByK	reimKAauskSQ9f	COMPLETE	2022-09-20 08:47:51.824153+00	2022-09-20 08:47:51.824181+00	1	P/2022/05/R/8
68	setDiksMn83K7	reimKUEIyXDetA	COMPLETE	2022-09-20 08:47:51.82423+00	2022-09-20 08:47:51.824259+00	1	P/2022/05/R/7
69	setCb41PcrHmO	reiml5iq0TVzp6	COMPLETE	2022-09-20 08:47:51.824306+00	2022-09-20 08:47:51.824335+00	1	P/2022/05/R/9
70	setlcYd0kfoBv	reimNM1P8qb3XS	COMPLETE	2022-09-20 08:47:51.824383+00	2022-09-20 08:47:51.824412+00	1	P/2022/05/R/10
71	setr9WSZQIwzH	reimrFgDFccXv9	COMPLETE	2022-09-20 08:47:51.82446+00	2022-09-20 08:47:51.824489+00	1	P/2022/05/R/3
72	sett283OqFZ42	reimuuvvDSapAh	COMPLETE	2022-09-20 08:47:51.824537+00	2022-09-20 08:47:51.824566+00	1	P/2022/05/R/4
73	set3ScziYvftR	reimxQfwQn2vSB	COMPLETE	2022-09-20 08:47:51.824613+00	2022-09-20 08:47:51.824642+00	1	P/2022/05/R/5
74	setUwjAkWcafS	reimiRGVADdoIt	COMPLETE	2022-09-20 08:47:51.82469+00	2022-09-20 08:47:51.824719+00	1	P/2022/05/R/2
75	setPAm1kjS3ld	reim9zPoX63qyx	COMPLETE	2022-09-20 08:47:51.824767+00	2022-09-20 08:47:51.824796+00	1	P/2022/05/R/1
76	set07HSTeqYTx	reimad8dQd65q8	COMPLETE	2022-09-20 08:47:51.824843+00	2022-09-20 08:47:51.824872+00	1	P/2022/04/R/27
77	setST8251H5Jr	reimhk1t2JezgC	COMPLETE	2022-09-20 08:47:51.824916+00	2022-09-20 08:47:51.824927+00	1	P/2022/04/R/28
78	setTGZBza3I48	reimapbaP4rd6m	COMPLETE	2022-09-20 08:47:51.824963+00	2022-09-20 08:47:51.824985+00	1	P/2022/04/R/26
79	set71RslsZm53	reim0uzF4CQrfv	COMPLETE	2022-09-20 08:47:51.825022+00	2022-09-20 08:47:51.825042+00	1	P/2022/04/R/21
80	setDCOvDMLWgp	reim2aiRHof8uf	COMPLETE	2022-09-20 08:47:51.825089+00	2022-09-20 08:47:51.825118+00	1	P/2022/04/R/14
81	set0E1WIAaUFt	reim5ULJ7gVG40	COMPLETE	2022-09-20 08:47:51.825166+00	2022-09-20 08:47:51.82519+00	1	P/2022/04/R/20
82	setXNNvb38eHN	reimHaaF2UZzXs	COMPLETE	2022-09-20 08:47:51.825229+00	2022-09-20 08:47:51.825258+00	1	P/2022/04/R/16
83	setdQvhTSJjIJ	reimj6e8QZkVon	COMPLETE	2022-09-20 08:47:51.825306+00	2022-09-20 08:47:51.825335+00	1	P/2022/04/R/23
84	setkXtd0l3JNq	reimLIKtE9x5Gq	COMPLETE	2022-09-20 08:47:51.825383+00	2022-09-20 08:47:51.825412+00	1	P/2022/04/R/18
85	setDGwWFhIIrG	reimLNl7P6yZ60	COMPLETE	2022-09-20 08:47:51.82546+00	2022-09-20 08:47:51.825489+00	1	P/2022/04/R/24
86	setIvuHHWWfQ7	reimo0xQELF5Om	COMPLETE	2022-09-20 08:47:51.825538+00	2022-09-20 08:47:51.825575+00	1	P/2022/04/R/19
87	setuEuBHtQhJJ	reimosKIcBRbFr	COMPLETE	2022-09-20 08:47:51.825908+00	2022-09-20 08:47:51.826388+00	1	P/2022/04/R/15
88	set8hrKnn02s5	reimp50f85KIJ6	COMPLETE	2022-09-20 08:47:51.827002+00	2022-09-20 08:47:51.827203+00	1	P/2022/04/R/17
89	setTLJ2yG0iME	reimqKq51CeH5R	COMPLETE	2022-09-20 08:47:51.827556+00	2022-09-20 08:47:51.827621+00	1	P/2022/04/R/13
90	setWklffaEIjT	reimVkyjTfI0fk	COMPLETE	2022-09-20 08:47:51.828021+00	2022-09-20 08:47:51.828567+00	1	P/2022/04/R/22
91	sethmLu8oDIGx	reim2P360jHuWg	COMPLETE	2022-09-20 08:47:51.829745+00	2022-09-20 08:47:51.82989+00	1	P/2022/03/R/17
92	setyuwUtkVB80	reim44c6rCEjFZ	COMPLETE	2022-09-20 08:47:51.830663+00	2022-09-20 08:47:51.830976+00	1	P/2022/03/R/2
93	setcGfp8wvVkh	reim4uhnCaijDm	COMPLETE	2022-09-20 08:47:51.832438+00	2022-09-20 08:47:51.833183+00	1	P/2022/03/R/13
94	setLSIPk4e2y7	reim6HoIExG9ip	COMPLETE	2022-09-20 08:47:51.83377+00	2022-09-20 08:47:51.834572+00	1	P/2022/03/R/15
95	settnQdWmPC0J	reim8P85qUFwub	COMPLETE	2022-09-20 08:47:51.837307+00	2022-09-20 08:47:51.838869+00	1	P/2022/03/R/8
96	setOcEEfhjFaz	reimAj1WFC7Cso	COMPLETE	2022-09-20 08:47:51.840527+00	2022-09-20 08:47:51.840967+00	1	P/2022/03/R/11
97	setZFCbhKDmlx	reimbLQoBvnHIc	COMPLETE	2022-09-20 08:47:51.841046+00	2022-09-20 08:47:51.842989+00	1	P/2022/03/R/5
98	setM00lSHnq5R	reimFQqG7b1TLN	COMPLETE	2022-09-20 08:47:51.843814+00	2022-09-20 08:47:51.844051+00	1	P/2022/03/R/9
99	setWksKskZS9T	reimHyqG6ycQsc	COMPLETE	2022-09-20 08:47:51.844874+00	2022-09-20 08:47:51.84499+00	1	P/2022/03/R/10
100	set4IB2lgkO81	reimIRnWM4OSjd	COMPLETE	2022-09-20 08:47:51.845486+00	2022-09-20 08:47:51.845671+00	1	P/2022/03/R/4
101	setNfPWvMVo9i	reimM5ApRLmRxs	COMPLETE	2022-09-20 08:47:51.859505+00	2022-09-20 08:47:51.859546+00	1	P/2022/03/R/1
102	setvN2PzkReuX	reimOQ0PjfcTrO	COMPLETE	2022-09-20 08:47:51.859594+00	2022-09-20 08:47:51.859625+00	1	P/2022/03/R/6
103	sethyy7hKOOJG	reimpO4DNwzKIP	COMPLETE	2022-09-20 08:47:51.859677+00	2022-09-20 08:47:51.859716+00	1	P/2022/03/R/7
104	setUiWCxpWU9W	reimq9xwG3c18j	COMPLETE	2022-09-20 08:47:51.859763+00	2022-09-20 08:47:51.85979+00	1	P/2022/03/R/14
105	setava6eJEse4	reimRbCnHMGfNE	COMPLETE	2022-09-20 08:47:51.859836+00	2022-09-20 08:47:51.859863+00	1	P/2022/03/R/16
106	setZMCqxqX9am	reimrrMZOocQOP	COMPLETE	2022-09-20 08:47:51.859909+00	2022-09-20 08:47:51.859936+00	1	P/2022/03/R/12
107	setgze09L0u2M	reimTuKaWlXWZp	COMPLETE	2022-09-20 08:47:51.859982+00	2022-09-20 08:47:51.860009+00	1	P/2022/03/R/18
108	set48IfVzq0yW	reimUC8ywjNm5X	COMPLETE	2022-09-20 08:47:51.860055+00	2022-09-20 08:47:51.860082+00	1	P/2022/03/R/3
109	set4nTmk49WTG	reimX2RpvsNWhL	COMPLETE	2022-09-20 08:47:51.860127+00	2022-09-20 08:47:51.860154+00	1	P/2022/04/R/1
110	seth6VNXcJYFY	reimZy8SIa2hrT	COMPLETE	2022-09-20 08:47:51.8602+00	2022-09-20 08:47:51.860227+00	1	P/2022/03/R/19
111	setRTRpBfxk74	reim0dzwluaekr	COMPLETE	2022-09-20 08:47:51.860272+00	2022-09-20 08:47:51.8603+00	1	P/2022/04/R/4
112	setGotI6V5Bc7	reim0jan70NxM0	COMPLETE	2022-09-20 08:47:51.860357+00	2022-09-20 08:47:51.860586+00	1	P/2022/04/R/12
113	setsUUIrSZ6FV	reim63zhXUcG3x	COMPLETE	2022-09-20 08:47:51.86078+00	2022-09-20 08:47:51.860809+00	1	P/2022/04/R/10
114	set0molu6y00L	reimazeO5ftv5e	COMPLETE	2022-09-20 08:47:51.86098+00	2022-09-20 08:47:51.861001+00	1	P/2022/04/R/2
115	setn5R9GYZJHa	reimcdR7M37m7u	COMPLETE	2022-09-20 08:47:51.861168+00	2022-09-20 08:47:51.861197+00	1	P/2022/04/R/5
116	setizmumgI16h	reimegLC8qXofr	COMPLETE	2022-09-20 08:47:51.861331+00	2022-09-20 08:47:51.86136+00	1	P/2022/04/R/6
117	setxTcm2NKM4z	reimEMBBTtWlaH	COMPLETE	2022-09-20 08:47:51.861416+00	2022-09-20 08:47:51.861444+00	1	P/2022/04/R/9
118	setuAmTQImATt	reimOkWc6NSeTV	COMPLETE	2022-09-20 08:47:51.861489+00	2022-09-20 08:47:51.861517+00	1	P/2022/04/R/7
119	set4EH2ck8BRV	reimPoi2fKYM43	COMPLETE	2022-09-20 08:47:51.861562+00	2022-09-20 08:47:51.86159+00	1	P/2022/04/R/11
120	setmykk0W2n2K	reimpzrHlcUWfA	COMPLETE	2022-09-20 08:47:51.861634+00	2022-09-20 08:47:51.861661+00	1	P/2022/04/R/3
121	setN6IN6qlZCZ	reims70NBaAJnI	COMPLETE	2022-09-20 08:47:51.861706+00	2022-09-20 08:47:51.861733+00	1	P/2022/04/R/8
122	setdZiDZ8D0ko	reim7RytpCGlTT	COMPLETE	2022-09-20 08:47:51.861778+00	2022-09-20 08:47:51.861805+00	1	P/2022/02/R/15
123	setpGurFkSvLj	reimAY92WzJm1Z	COMPLETE	2022-09-20 08:47:51.86185+00	2022-09-20 08:47:51.861877+00	1	P/2022/02/R/10
124	setsdctMW3RGI	reimgI9wRdvRSq	COMPLETE	2022-09-20 08:47:51.861922+00	2022-09-20 08:47:51.861949+00	1	P/2022/02/R/16
125	setwfuGqOD7Fj	reimgttOEE3GzU	COMPLETE	2022-09-20 08:47:51.861994+00	2022-09-20 08:47:51.862021+00	1	P/2022/02/R/8
126	setU5bHAY0duH	reimHXatGajJAF	COMPLETE	2022-09-20 08:47:51.862066+00	2022-09-20 08:47:51.862093+00	1	P/2022/02/R/9
127	setSB57y0GWNi	reimlRxqgraaSZ	COMPLETE	2022-09-20 08:47:51.862139+00	2022-09-20 08:47:51.862166+00	1	P/2022/02/R/13
128	setJVeW5M8DV0	reimMFnVXze33C	COMPLETE	2022-09-20 08:47:51.86221+00	2022-09-20 08:47:51.862238+00	1	P/2022/02/R/14
129	set4oKGBzriLU	reimNl0BNyTaqZ	COMPLETE	2022-09-20 08:47:51.862282+00	2022-09-20 08:47:51.86231+00	1	P/2022/02/R/6
130	setPB71bu3fMn	reimOEym6ene9g	COMPLETE	2022-09-20 08:47:51.862354+00	2022-09-20 08:47:51.862381+00	1	P/2022/02/R/12
131	setL6I4NXOECq	reimoUn2AZn8nN	COMPLETE	2022-09-20 08:47:51.862538+00	2022-09-20 08:47:51.862568+00	1	P/2022/02/R/7
132	setJa7ohOyOVq	reimuZORFOP1eU	COMPLETE	2022-09-20 08:47:51.862617+00	2022-09-20 08:47:51.862646+00	1	P/2022/02/R/11
133	setazA7r4XEAX	reim0xadXajpKe	COMPLETE	2022-09-20 08:47:51.862704+00	2022-09-20 08:47:51.862731+00	1	P/2022/02/R/3
134	set3Jk3g3Z6Zy	reim259bHDvtKo	COMPLETE	2022-09-20 08:47:51.862776+00	2022-09-20 08:47:51.862803+00	1	P/2022/02/R/1
135	setp4P01OhM7P	reim4PrtYFGswm	COMPLETE	2022-09-20 08:47:51.862848+00	2022-09-20 08:47:51.862875+00	1	P/2022/02/R/4
136	setCsqR7hm2Yd	reimdv6QjZULGh	COMPLETE	2022-09-20 08:47:51.862921+00	2022-09-20 08:47:51.862948+00	1	P/2022/02/R/5
137	setHcR9AfVjG7	reimtGSoHV9eOq	COMPLETE	2022-09-20 08:47:51.862994+00	2022-09-20 08:47:51.863021+00	1	P/2022/02/R/2
138	set8I1KlM4ViY	reim3Z8MRqSOb4	COMPLETE	2022-09-20 08:47:51.863066+00	2022-09-20 08:47:51.863093+00	1	P/2022/01/R/13
139	setXTEjf2wY78	reim96dgvtsQLS	COMPLETE	2022-09-20 08:47:51.863148+00	2022-09-20 08:47:51.863178+00	1	P/2022/01/R/12
140	setwQTDDrGSJN	reimHEsSEj7WOF	COMPLETE	2022-09-20 08:47:51.86329+00	2022-09-20 08:47:51.863335+00	1	P/2022/01/R/15
141	setRaxYbWGAop	reimmJmfHydjTQ	COMPLETE	2022-09-20 08:47:51.863385+00	2022-09-20 08:47:51.863414+00	1	P/2022/01/R/14
142	setsSgEIicV7I	reimnTXklcfx8j	COMPLETE	2022-09-20 08:47:51.863471+00	2022-09-20 08:47:51.863498+00	1	P/2022/01/R/16
143	setTlzHY8Idf9	reimUQB0yvKE2H	COMPLETE	2022-09-20 08:47:51.863544+00	2022-09-20 08:47:51.863571+00	1	P/2022/01/R/11
144	setIeo4DDtxHT	reimHw5QUpoQUA	COMPLETE	2022-09-20 08:47:51.863616+00	2022-09-20 08:47:51.863644+00	1	P/2022/01/R/9
145	setMh1EJsrbhI	reimtPqiobU07o	COMPLETE	2022-09-20 08:47:51.863689+00	2022-09-20 08:47:51.863717+00	1	P/2022/01/R/10
146	set47jUdkX7df	reimdgZAnTYkyF	COMPLETE	2022-09-20 08:47:51.863762+00	2022-09-20 08:47:51.863789+00	1	P/2022/01/R/4
147	setkga8K7pOvH	reimh25CqiYFmz	COMPLETE	2022-09-20 08:47:51.863834+00	2022-09-20 08:47:51.863862+00	1	P/2022/01/R/5
148	seth0ZuGB45cU	reimWim0WoP21K	COMPLETE	2022-09-20 08:47:51.863908+00	2022-09-20 08:47:51.863935+00	1	P/2022/01/R/7
149	setQNMA55r3t6	reimY3Ws7FdKI0	COMPLETE	2022-09-20 08:47:51.86398+00	2022-09-20 08:47:51.864008+00	1	P/2022/01/R/8
150	setxw08fdZkJm	reimzvABRys4JB	COMPLETE	2022-09-20 08:47:51.864053+00	2022-09-20 08:47:51.86408+00	1	P/2022/01/R/6
151	setYWyqpn2e7h	reim4sBDuBc9Pt	COMPLETE	2022-09-20 08:47:51.87007+00	2022-09-20 08:47:51.870117+00	1	P/2021/12/R/25
152	set5zxN39ACYT	reim8V4mh3dtgf	COMPLETE	2022-09-20 08:47:51.870177+00	2022-09-20 08:47:51.87021+00	1	P/2021/12/R/24
153	set8pZeam5Xmh	reimEI6qpFxCXR	COMPLETE	2022-09-20 08:47:51.870262+00	2022-09-20 08:47:51.870292+00	1	P/2021/12/R/18
154	setVAi6qgTKaK	reimKhDIL8x231	COMPLETE	2022-09-20 08:47:51.870435+00	2022-09-20 08:47:51.870465+00	1	P/2021/12/R/21
155	setIgWi3knZi2	reimqy792bKbjL	COMPLETE	2022-09-20 08:47:51.870514+00	2022-09-20 08:47:51.870544+00	1	P/2021/12/R/19
156	set45twRgTDmG	reimR6FirDraLC	COMPLETE	2022-09-20 08:47:51.870593+00	2022-09-20 08:47:51.870622+00	1	P/2021/12/R/20
157	set0N7wWCQJdo	reimTIgDJ8TaLa	COMPLETE	2022-09-20 08:47:51.870671+00	2022-09-20 08:47:51.8707+00	1	P/2021/12/R/22
158	setO0UbNqJarw	reimvIkvR2x3gf	COMPLETE	2022-09-20 08:47:51.870743+00	2022-09-20 08:47:51.870762+00	1	P/2021/12/R/23
159	set69I0nRQOSb	reimVm757JWven	COMPLETE	2022-09-20 08:47:51.870799+00	2022-09-20 08:47:51.870828+00	1	P/2021/12/R/26
160	setvuXeevsFUi	reim3oIVrBLR4A	COMPLETE	2022-09-20 08:47:51.870872+00	2022-09-20 08:47:51.870892+00	1	P/2021/12/R/10
161	setxPPoKPROKS	reim7dRnQrZ4gq	COMPLETE	2022-09-20 08:47:51.87094+00	2022-09-20 08:47:51.870969+00	1	P/2021/12/R/3
162	set9cHrSJF4W7	reimC0X9RmP78z	COMPLETE	2022-09-20 08:47:51.871017+00	2022-09-20 08:47:51.871046+00	1	P/2021/12/R/5
163	set7dGYd4zqWx	reimdOwXsZszou	COMPLETE	2022-09-20 08:47:51.871094+00	2022-09-20 08:47:51.871123+00	1	P/2021/12/R/9
164	setqc9v7zLUau	reimfUh2zXgVIw	COMPLETE	2022-09-20 08:47:51.871171+00	2022-09-20 08:47:51.8712+00	1	P/2021/12/R/7
165	setIadhiifLvi	reimKQseRs6OyS	COMPLETE	2022-09-20 08:47:51.871248+00	2022-09-20 08:47:51.871277+00	1	P/2021/12/R/4
166	setUMqw9puNZC	reimlmR3MalDTS	COMPLETE	2022-09-20 08:47:51.871403+00	2022-09-20 08:47:51.871428+00	1	P/2021/12/R/11
167	setOkP5YhBDUX	reimN6QK1thbzP	COMPLETE	2022-09-20 08:47:51.871485+00	2022-09-20 08:47:51.871522+00	1	P/2021/12/R/15
168	setfkCx1C0aF7	reimPiGJOk6k2m	COMPLETE	2022-09-20 08:47:51.871716+00	2022-09-20 08:47:51.871856+00	1	P/2021/12/R/8
169	setMFzLqjWn0w	reimry3avp5Bfx	COMPLETE	2022-09-20 08:47:51.871902+00	2022-09-20 08:47:51.871929+00	1	P/2021/12/R/6
170	setiTgqNEQmbv	reimTXCPHfMAtL	COMPLETE	2022-09-20 08:47:51.872119+00	2022-09-20 08:47:51.872148+00	1	P/2021/12/R/12
171	setsOLPmsclEl	reimuFXDylMOQ5	COMPLETE	2022-09-20 08:47:51.87237+00	2022-09-20 08:47:51.872391+00	1	P/2021/12/R/16
172	sett8PY0YfPTP	reimyJDGFMXl9q	COMPLETE	2022-09-20 08:47:51.872549+00	2022-09-20 08:47:51.872577+00	1	P/2021/12/R/14
173	setosMugG1BZB	reimZlL2cKDmqQ	COMPLETE	2022-09-20 08:47:51.872622+00	2022-09-20 08:47:51.87265+00	1	P/2021/12/R/17
174	set7fW1a59Iah	reimzWqPnZflvp	COMPLETE	2022-09-20 08:47:51.872695+00	2022-09-20 08:47:51.872722+00	1	P/2021/12/R/13
175	setJUM1qUuD0v	reimzZDyqtTR44	COMPLETE	2022-09-20 08:47:51.872767+00	2022-09-20 08:47:51.872795+00	1	P/2021/12/R/2
176	setO6eQ3l8ZTW	reimkGTejmdR29	COMPLETE	2022-09-20 08:47:51.87284+00	2022-09-20 08:47:51.872867+00	1	P/2021/12/R/1
177	setNVTcPkZ6on	reimGo4jgmkxgu	COMPLETE	2022-09-20 08:47:51.872913+00	2022-09-20 08:47:51.87294+00	1	P/2021/11/R/6
178	set6GUp6tcEEp	reimuryMHcTPqS	COMPLETE	2022-09-20 08:47:51.872985+00	2022-09-20 08:47:51.873012+00	1	P/2021/11/R/5
179	settnd33XXXUV	reim4Ky9i1G9Kr	COMPLETE	2022-09-20 08:47:51.873057+00	2022-09-20 08:47:51.873084+00	1	P/2021/11/R/3
180	setqGwGhrDyFI	reimBO6Mv4Qnt8	COMPLETE	2022-09-20 08:47:51.873129+00	2022-09-20 08:47:51.873156+00	1	P/2021/11/R/4
181	set8c1zvWojUn	reimRz56rpQsE7	COMPLETE	2022-09-20 08:47:51.873201+00	2022-09-20 08:47:51.873377+00	1	P/2021/11/R/2
182	setuDRccuk3ZY	reimSh5EFeUxBp	COMPLETE	2022-09-20 08:47:51.87347+00	2022-09-20 08:47:51.873507+00	1	P/2021/11/R/1
183	setD0FxMB9wgI	reim1yN4sXTxUv	COMPLETE	2022-09-20 08:47:51.873575+00	2022-09-20 08:47:51.873615+00	1	P/2021/10/R/3
184	setapiOdjBgFM	reim5qVte0TNYh	COMPLETE	2022-09-20 08:47:51.873661+00	2022-09-20 08:47:51.873688+00	1	P/2021/10/R/6
185	setfco2Zf8Bhv	reim6vFkSNiwz5	COMPLETE	2022-09-20 08:47:51.873734+00	2022-09-20 08:47:51.873761+00	1	P/2021/10/R/7
186	setW46pKF7T4Z	reimOlkDOh2UGE	COMPLETE	2022-09-20 08:47:51.873806+00	2022-09-20 08:47:51.873833+00	1	P/2021/10/R/5
187	setYcoiZJOBkw	reimOqdMXmFM12	COMPLETE	2022-09-20 08:47:51.873879+00	2022-09-20 08:47:51.873906+00	1	P/2021/10/R/4
188	setf9EYZDnHpj	reimPJD5oAnocg	COMPLETE	2022-09-20 08:47:51.873951+00	2022-09-20 08:47:51.873979+00	1	P/2021/10/R/2
189	setID9JbDdOJf	reimWOE3evTwSF	COMPLETE	2022-09-20 08:47:51.874023+00	2022-09-20 08:47:51.87405+00	1	P/2021/10/R/1
190	setI5KZUaZTJB	reim0kuGWiPtFf	COMPLETE	2022-09-20 08:47:51.874095+00	2022-09-20 08:47:51.874123+00	1	P/2021/09/R/19
191	setoj9oE3CToc	reim0nwzia1h2t	COMPLETE	2022-09-20 08:47:51.874167+00	2022-09-20 08:47:51.874194+00	1	P/2021/09/R/27
192	setNQPb1pIVSZ	reim6yNBIgEcAZ	COMPLETE	2022-09-20 08:47:51.874239+00	2022-09-20 08:47:51.874266+00	1	P/2021/09/R/25
193	setBgSo93ruxj	reimbFci0QSgKr	COMPLETE	2022-09-20 08:47:51.874311+00	2022-09-20 08:47:51.874338+00	1	P/2021/09/R/28
194	setFjKBjHQ01G	reimhgMByHKZUX	COMPLETE	2022-09-20 08:47:51.874397+00	2022-09-20 08:47:51.87454+00	1	P/2021/09/R/21
195	setebUutDZHeo	reimICJTmIn4kc	COMPLETE	2022-09-20 08:47:51.874596+00	2022-09-20 08:47:51.874624+00	1	P/2021/09/R/22
196	setszPgxuxwLp	reimJeucH6013K	COMPLETE	2022-09-20 08:47:51.874668+00	2022-09-20 08:47:51.874695+00	1	P/2021/09/R/18
197	setmLzx1yk8yi	reimOR7xV95PGa	COMPLETE	2022-09-20 08:47:51.87474+00	2022-09-20 08:47:51.874767+00	1	P/2021/09/R/26
198	set8C6wTvgMnF	reimQ18CEIcK6R	COMPLETE	2022-09-20 08:47:51.874813+00	2022-09-20 08:47:51.87484+00	1	P/2021/09/R/23
199	setu2LSD0aj5d	reimW0r9GHIOBl	COMPLETE	2022-09-20 08:47:51.874885+00	2022-09-20 08:47:51.874912+00	1	P/2021/09/R/24
200	set2DYrdlPs9H	reimw981ttF3Am	COMPLETE	2022-09-20 08:47:51.874957+00	2022-09-20 08:47:51.874984+00	1	P/2021/09/R/20
201	setlOgL4QsSHm	reim5NRAeRIKvC	COMPLETE	2022-09-20 08:47:52.135872+00	2022-09-20 08:47:52.13592+00	1	P/2021/09/R/17
202	setoDPXAbJVKE	reimKMjrt5Alzv	COMPLETE	2022-09-20 08:47:52.135977+00	2022-09-20 08:47:52.136007+00	1	P/2021/09/R/11
203	setdKKjOsJFQT	reimlmU2VmDQfi	COMPLETE	2022-09-20 08:47:52.136059+00	2022-09-20 08:47:52.136089+00	1	P/2021/09/R/14
204	setp6F16p8WGG	reimOLyU8dPMIC	COMPLETE	2022-09-20 08:47:52.13614+00	2022-09-20 08:47:52.136169+00	1	P/2021/09/R/16
205	setKuh6lPAIoU	reimOyBjNfxXl6	COMPLETE	2022-09-20 08:47:52.136218+00	2022-09-20 08:47:52.136247+00	1	P/2021/09/R/13
206	setiqT5I1nAPC	reimuIJOi0YHFw	COMPLETE	2022-09-20 08:47:52.136296+00	2022-09-20 08:47:52.136325+00	1	P/2021/09/R/15
207	setmPOMFfkp4F	reimzRqvxvT2Qg	COMPLETE	2022-09-20 08:47:52.136801+00	2022-09-20 08:47:52.137067+00	1	P/2021/09/R/12
208	setWTpwg4RovE	reim06HLC2nYuL	COMPLETE	2022-09-20 08:47:52.137145+00	2022-09-20 08:47:52.137598+00	1	P/2021/09/R/8
209	set40zby2tfZG	reim1ZP27BcTtK	COMPLETE	2022-09-20 08:47:52.13782+00	2022-09-20 08:47:52.137907+00	1	P/2021/09/R/5
210	setjlqb0ijG5p	reimlBDOZSnxnc	COMPLETE	2022-09-20 08:47:52.138065+00	2022-09-20 08:47:52.138088+00	1	P/2021/09/R/10
211	set1iQc9Aj7FQ	reimRv63PXtevO	COMPLETE	2022-09-20 08:47:52.138139+00	2022-09-20 08:47:52.138401+00	1	P/2021/09/R/9
212	set5MygblkDjN	reimTaHuQCU51d	COMPLETE	2022-09-20 08:47:52.139025+00	2022-09-20 08:47:52.139115+00	1	P/2021/09/R/4
213	setEQaoy2E3p5	reimUkyMiLsEJG	COMPLETE	2022-09-20 08:47:52.139169+00	2022-09-20 08:47:52.139198+00	1	P/2021/09/R/6
214	setljJSrcbhhw	reimyIKJwIBAPf	COMPLETE	2022-09-20 08:47:52.151007+00	2022-09-20 08:47:52.151593+00	1	P/2021/09/R/7
215	setoUlfPVilij	reimj9nMjpVDjX	COMPLETE	2022-09-20 08:47:52.15176+00	2022-09-20 08:47:52.151818+00	1	P/2021/09/R/2
216	setPDVdChFccy	reimwa6MME9059	COMPLETE	2022-09-20 08:47:52.152+00	2022-09-20 08:47:52.152189+00	1	P/2021/09/R/3
217	setRgyGDsFShB	reimyWTvWVgY0D	COMPLETE	2022-09-20 08:47:52.152316+00	2022-09-20 08:47:52.152534+00	1	P/2021/09/R/1
218	setkZYPYBVfTg	reimFWQZC5E4S0	COMPLETE	2022-09-20 08:47:52.152639+00	2022-09-20 08:47:52.152695+00	1	P/2021/08/R/6
219	setJJju741FFg	reimnI4LHXlyG7	COMPLETE	2022-09-20 08:47:52.152779+00	2022-09-20 08:47:52.152821+00	1	P/2021/08/R/7
220	setRISbQrl2qS	reimacWy4G0x7p	COMPLETE	2022-09-20 08:47:52.152896+00	2022-09-20 08:47:52.152939+00	1	P/2021/07/R/5
221	setoWnez7K7u8	reimG37HYNnSQr	COMPLETE	2022-09-20 08:47:52.153011+00	2022-09-20 08:47:52.153051+00	1	P/2021/07/R/6
222	set7GTJ65dqXR	reimjH3py8giuH	COMPLETE	2022-09-20 08:47:52.15314+00	2022-09-20 08:47:52.15318+00	1	P/2021/08/R/2
223	setGDT4k1lQf4	reimlx82ge41YV	COMPLETE	2022-09-20 08:47:52.153253+00	2022-09-20 08:47:52.153295+00	1	P/2021/08/R/4
224	setqXmQh9Pm0M	reimm6MtpMRnCC	COMPLETE	2022-09-20 08:47:52.15337+00	2022-09-20 08:47:52.153412+00	1	P/2021/08/R/5
225	setjVNiPVR1jN	reimmI9lRniCJr	COMPLETE	2022-09-20 08:47:52.153491+00	2022-09-20 08:47:52.153919+00	1	P/2021/08/R/3
226	setCs9kR5F9wG	reimRheySEVfV5	COMPLETE	2022-09-20 08:47:52.154024+00	2022-09-20 08:47:52.154058+00	1	P/2021/08/R/1
227	set7RuRljR2US	reimtZT3OfpqsH	COMPLETE	2022-09-20 08:47:52.154114+00	2022-09-20 08:47:52.154145+00	1	P/2021/07/R/7
228	setAkz6uawLzJ	reim0ar7e7cl1B	COMPLETE	2022-09-20 08:47:52.154197+00	2022-09-20 08:47:52.154227+00	1	P/2021/04/R/5
229	set8bqJuj42zM	reim2ddpn9CgIM	COMPLETE	2022-09-20 08:47:52.154278+00	2022-09-20 08:47:52.154307+00	1	P/2021/06/R/3
230	setbyBcekbrNS	reim4QHN8bo5dL	COMPLETE	2022-09-20 08:47:52.154357+00	2022-09-20 08:47:52.154386+00	1	P/2021/04/R/15
231	setHnAi3uuDk4	reim7hf6u5CIsz	COMPLETE	2022-09-20 08:47:52.154435+00	2022-09-20 08:47:52.154464+00	1	P/2021/04/R/1
232	sethlKpGuwoJ0	reimALBhmYbkZz	COMPLETE	2022-09-20 08:47:52.154769+00	2022-09-20 08:47:52.154821+00	1	P/2021/04/R/18
233	setpXKES1mcgV	reimApNMfycYDM	COMPLETE	2022-09-20 08:47:52.154906+00	2022-09-20 08:47:52.15495+00	1	P/2021/04/R/7
234	setzShIVVgOwy	reimAW3UcDsYc9	COMPLETE	2022-09-20 08:47:52.155032+00	2022-09-20 08:47:52.155076+00	1	P/2021/04/R/10
235	setsFBsWtVA0A	reimbExYNN4uAr	COMPLETE	2022-09-20 08:47:52.155179+00	2022-09-20 08:47:52.155333+00	1	P/2021/04/R/16
236	set22F2Ujz6bL	reimbRxTUFiuhl	COMPLETE	2022-09-20 08:47:52.155433+00	2022-09-20 08:47:52.155477+00	1	P/2021/04/R/4
237	setRPTkaLEA6A	reimbT0YDHy6EB	COMPLETE	2022-09-20 08:47:52.155562+00	2022-09-20 08:47:52.155603+00	1	P/2021/04/R/6
238	setWoXaZ315lj	reimc90pbbk0t3	COMPLETE	2022-09-20 08:47:52.155686+00	2022-09-20 08:47:52.155728+00	1	P/2021/04/R/19
239	setnVhKqxQBQU	reimCeZihHkHzD	COMPLETE	2022-09-20 08:47:52.155811+00	2022-09-20 08:47:52.155854+00	1	P/2021/07/R/1
240	setnBGGIIgsXv	reimEyMVFd0b2C	COMPLETE	2022-09-20 08:47:52.155935+00	2022-09-20 08:47:52.155977+00	1	P/2021/07/R/4
241	setkffhZNy5u8	reimfxqmcofdub	COMPLETE	2022-09-20 08:47:52.156057+00	2022-09-20 08:47:52.156099+00	1	P/2021/04/R/12
242	setK2qGXUVYeK	reimjc9STOOUXk	COMPLETE	2022-09-20 08:47:52.156176+00	2022-09-20 08:47:52.156217+00	1	P/2021/06/R/1
243	set1Q9cbXdFpo	reimjoFxMWVjo4	COMPLETE	2022-09-20 08:47:52.156316+00	2022-09-20 08:47:52.156504+00	1	P/2021/04/R/11
244	setIRZ77y74Iz	reimLT0dYtIS3T	COMPLETE	2022-09-20 08:47:52.156608+00	2022-09-20 08:47:52.156654+00	1	P/2021/06/R/4
245	setIAJr6wrvqe	reimmMOvMIeJch	COMPLETE	2022-09-20 08:47:52.15674+00	2022-09-20 08:47:52.156784+00	1	P/2021/07/R/3
246	setiC4kFrWhDq	reimoeF805mwct	COMPLETE	2022-09-20 08:47:52.156865+00	2022-09-20 08:47:52.156913+00	1	P/2021/04/R/9
247	set4utLw6FooE	reimOO96buaT6r	COMPLETE	2022-09-20 08:47:52.157001+00	2022-09-20 08:47:52.157047+00	1	P/2021/04/R/14
248	setdp4ha7hDyp	reimOyxJylgV0D	COMPLETE	2022-09-20 08:47:52.157133+00	2022-09-20 08:47:52.157179+00	1	P/2021/05/R/1
249	setElIlIKoxzB	reimP6wzvtmPz9	COMPLETE	2022-09-20 08:47:52.157259+00	2022-09-20 08:47:52.1573+00	1	P/2021/04/R/17
250	setYcZpeBJ801	reimrmENfuZaNy	COMPLETE	2022-09-20 08:47:52.157379+00	2022-09-20 08:47:52.157421+00	1	P/2021/04/R/3
251	set94gxAHNFqi	reimrYLmZPHMid	COMPLETE	2022-09-20 08:47:52.18222+00	2022-09-20 08:47:52.182258+00	1	P/2021/04/R/8
252	setnyEVTtuz1E	reimswrdQBVx7I	COMPLETE	2022-09-20 08:47:52.18231+00	2022-09-20 08:47:52.182325+00	1	P/2021/04/R/13
253	setDnWZq3KSJq	reimvET2ReVpzw	COMPLETE	2022-09-20 08:47:52.182368+00	2022-09-20 08:47:52.182393+00	1	P/2021/06/R/2
254	setTMM90SzQUX	reimVPDY0njHkG	COMPLETE	2022-09-20 08:47:52.182429+00	2022-09-20 08:47:52.18245+00	1	P/2021/07/R/2
255	setvGxsBVkZh4	reimYTokyRgXGY	COMPLETE	2022-09-20 08:47:52.182501+00	2022-09-20 08:47:52.18253+00	1	P/2021/04/R/2
256	setzhjuqQ6Pl5	reimYKDswIkdVo	PENDING	2022-09-20 08:51:34.07695+00	2022-09-20 08:51:34.077116+00	1	P/2022/09/R/19
257	set0SnAq66Zbq	reimRyIMU9MJzg	PENDING	2022-09-20 08:57:03.080411+00	2022-09-20 08:57:03.080539+00	1	P/2022/09/R/20
258	setzZCuAPxIsB	reimdGLTKKZwpK	PENDING	2022-09-29 12:09:26.484722+00	2022-09-29 12:09:26.484765+00	1	P/2022/09/R/21
\.


--
-- Data for Name: sage_intacct_attributes_count; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sage_intacct_attributes_count (id, accounts_count, items_count, vendors_count, employees_count, departments_count, classes_count, customers_count, projects_count, locations_count, expense_types_count, tax_details_count, cost_codes_count, cost_types_count, user_defined_dimensions_details, charge_card_accounts_count, payment_accounts_count, expense_payment_types_count, allocations_count, created_at, updated_at, workspace_id) FROM stdin;
1	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	2022-09-20 08:38:48.66191+00	2022-09-20 08:38:48.661952+00	1
\.


--
-- Data for Name: sage_intacct_credentials; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sage_intacct_credentials (id, si_user_id, si_company_id, si_company_name, si_user_password, created_at, updated_at, workspace_id, is_expired, refresh_token, access_token, access_token_expires_at) FROM stdin;
1	team_cs	FyleMPP-DEV2	FyleMPP-DEV	gAAAAABjKXwVzRsxpid8IRVcaHGmjh-n8HoNrbe9PgWsXUEGdZ8WMcu9OaV_CFdVsKiyM714fc3hYCZPU4szITy-PZtQQxqU5Q==	2022-09-20 08:38:48.66191+00	2022-09-20 08:38:48.661952+00	1	f	\N	\N	\N
\.


--
-- Data for Name: sage_intacct_reimbursement_lineitems; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sage_intacct_reimbursement_lineitems (id, amount, record_key, created_at, updated_at, sage_intacct_reimbursement_id) FROM stdin;
\.


--
-- Data for Name: sage_intacct_reimbursements; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sage_intacct_reimbursements (id, account_id, employee_id, memo, payment_description, created_at, updated_at, expense_group_id) FROM stdin;
\.


--
-- Data for Name: task_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.task_logs (id, type, task_id, status, detail, sage_intacct_errors, created_at, updated_at, bill_id, expense_report_id, expense_group_id, workspace_id, charge_card_transaction_id, ap_payment_id, sage_intacct_reimbursement_id, journal_entry_id, supdoc_id, is_retired, triggered_by, re_attempt_export, is_attachment_upload_failed) FROM stdin;
2	CREATING_BILLS	\N	FAILED	\N	[{"correction": "Use tax details that belong to the tax solution.", "expense_group_id": 1, "long_description": "Tax detail Capital Goods Imported cannot be used in this transaction because it does not belong to tax solution Australia - GST. [Support ID: Y@whFEB036~YzQ2cP0p2Zz-Iv9WTjEPDwAAABY]", "short_description": "Bills error"}, {"correction": "Check the transaction for errors or inconsistencies, then try again.", "expense_group_id": 1, "long_description": "Currently, we can't create the transaction 'Reimbursable expense - C/2022/09/R/21'.", "short_description": "Bills error"}]	2022-09-20 08:48:35.694698+00	2022-09-28 11:56:34.693143+00	\N	\N	1	1	\N	\N	\N	\N	\N	f	\N	f	f
4	CREATING_BILLS	\N	FAILED	\N	[{"correction": "Use tax details that belong to the tax solution.", "expense_group_id": 3, "long_description": "Tax detail Capital Goods Imported cannot be used in this transaction because it does not belong to tax solution Australia - GST. [Support ID: R8nHGEB032~YzQ2dP0F2Qk-@XXWEOh26wAAAAs]", "short_description": "Bills error"}, {"correction": "Check the transaction for errors or inconsistencies, then try again.", "expense_group_id": 3, "long_description": "Currently, we can't create the transaction 'Corporate Credit Card expense - C/2022/09/R/23 - 28/09/2022'.", "short_description": "Bills error"}]	2022-09-20 08:57:02.308154+00	2022-09-28 11:56:37.749629+00	\N	\N	3	1	\N	\N	\N	\N	\N	f	\N	f	f
3	CREATING_BILLS	\N	FAILED	\N	[{"correction": "Use tax details that belong to the tax solution.", "expense_group_id": 2, "long_description": "Tax detail Capital Goods Imported cannot be used in this transaction because it does not belong to tax solution Australia - GST. [Support ID: MLsapEB032~YzQ2cP0t2Y9-GgzWugr3IAAAAAU]", "short_description": "Bills error"}, {"correction": "Check the transaction for errors or inconsistencies, then try again.", "expense_group_id": 2, "long_description": "Currently, we can't create the transaction 'Corporate Credit Card expense - C/2022/09/R/22 - 28/09/2022'.", "short_description": "Bills error"}]	2022-09-20 08:51:33.345793+00	2022-09-28 11:56:33.933636+00	\N	\N	2	1	\N	\N	\N	\N	\N	f	\N	f	f
\.


--
-- Data for Name: update_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.update_logs (id, table_name, old_data, new_data, difference, workspace_id, created_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (password, last_login, id, email, user_id, full_name, active, staff, admin) FROM stdin;
	\N	1	ashwin.t@fyle.in	usqywo0f3nBY		t	f	f
\.


--
-- Data for Name: workspace_schedules; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workspace_schedules (id, enabled, start_datetime, interval_hours, schedule_id, workspace_id, additional_email_options, emails_selected, error_count, created_at, updated_at, is_real_time_export_enabled) FROM stdin;
\.


--
-- Data for Name: workspaces; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workspaces (id, name, fyle_org_id, last_synced_at, created_at, updated_at, destination_synced_at, source_synced_at, cluster_domain, ccc_last_synced_at, onboarding_state, app_version) FROM stdin;
1	Fyle For Arkham Asylum	or79Cob97KSh	2022-09-20 08:56:50.098426+00	2022-09-20 08:38:03.352044+00	2022-09-20 08:56:50.098865+00	2022-09-28 11:56:39.11276+00	2022-09-28 11:55:42.90121+00	https://staging.fyle.tech	\N	IMPORT_SETTINGS	v1
\.


--
-- Data for Name: workspaces_user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workspaces_user (id, workspace_id, user_id, created_at) FROM stdin;
1	1	1	2024-12-23 10:52:45.370215+00
\.


--
-- Name: ap_payment_lineitems_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ap_payment_lineitems_id_seq', 8, true);


--
-- Name: ap_payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ap_payments_id_seq', 8, true);


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 228, true);


--
-- Name: category_mappings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.category_mappings_id_seq', 140, true);


--
-- Name: cost_codes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.cost_codes_id_seq', 1, false);


--
-- Name: cost_types_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.cost_types_id_seq', 1, false);


--
-- Name: dependent_fields_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.dependent_fields_id_seq', 1, false);


--
-- Name: dimension_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.dimension_details_id_seq', 1, false);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 57, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 273, true);


--
-- Name: django_q_ormq_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_q_ormq_id_seq', 89, true);


--
-- Name: django_q_schedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_q_schedule_id_seq', 96, true);


--
-- Name: employee_mappings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.employee_mappings_id_seq', 5, true);


--
-- Name: errors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.errors_id_seq', 1, false);


--
-- Name: expense_attributes_deletion_cache_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.expense_attributes_deletion_cache_id_seq', 1, false);


--
-- Name: expense_fields_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.expense_fields_id_seq', 1, false);


--
-- Name: expense_filters_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.expense_filters_id_seq', 1, false);


--
-- Name: expense_group_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.expense_group_settings_id_seq', 5, true);


--
-- Name: failed_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.failed_events_id_seq', 1, false);


--
-- Name: feature_configs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.feature_configs_id_seq', 1, true);


--
-- Name: fyle_accounting_mappings_destinationattribute_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_accounting_mappings_destinationattribute_id_seq', 955, true);


--
-- Name: fyle_accounting_mappings_expenseattribute_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_accounting_mappings_expenseattribute_id_seq', 3278, true);


--
-- Name: fyle_accounting_mappings_mapping_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_accounting_mappings_mapping_id_seq', 74, true);


--
-- Name: fyle_accounting_mappings_mappingsetting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_accounting_mappings_mappingsetting_id_seq', 15, true);


--
-- Name: fyle_expense_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_expense_id_seq', 13, true);


--
-- Name: fyle_expensegroup_expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_expensegroup_expenses_id_seq', 25, true);


--
-- Name: fyle_expensegroup_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_expensegroup_id_seq', 9, true);


--
-- Name: fyle_rest_auth_authtokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_rest_auth_authtokens_id_seq', 1, true);


--
-- Name: fyle_sync_timestamps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fyle_sync_timestamps_id_seq', 1, true);


--
-- Name: import_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.import_logs_id_seq', 1, false);


--
-- Name: intacct_sync_timestamps_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.intacct_sync_timestamps_id_seq', 1, true);


--
-- Name: journal_entries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.journal_entries_id_seq', 10, true);


--
-- Name: journal_entry_lineitems_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.journal_entry_lineitems_id_seq', 10, true);


--
-- Name: last_export_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.last_export_details_id_seq', 5, true);


--
-- Name: location_entity_mappings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.location_entity_mappings_id_seq', 1, true);


--
-- Name: mappings_generalmapping_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.mappings_generalmapping_id_seq', 1, true);


--
-- Name: reimbursements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reimbursements_id_seq', 260, true);


--
-- Name: sage_intacct_attributes_count_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_attributes_count_id_seq', 2, false);


--
-- Name: sage_intacct_bill_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_bill_id_seq', 24, true);


--
-- Name: sage_intacct_billlineitem_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_billlineitem_id_seq', 24, true);


--
-- Name: sage_intacct_chargecardtransaction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_chargecardtransaction_id_seq', 10, true);


--
-- Name: sage_intacct_chargecardtransactionlineitem_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_chargecardtransactionlineitem_id_seq', 10, true);


--
-- Name: sage_intacct_expensereport_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_expensereport_id_seq', 26, true);


--
-- Name: sage_intacct_expensereportlineitem_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_expensereportlineitem_id_seq', 26, true);


--
-- Name: sage_intacct_reimbursement_lineitems_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_reimbursement_lineitems_id_seq', 18, true);


--
-- Name: sage_intacct_reimbursements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sage_intacct_reimbursements_id_seq', 18, true);


--
-- Name: tasks_tasklog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tasks_tasklog_id_seq', 42, true);


--
-- Name: update_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.update_logs_id_seq', 1, false);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_user_id_seq', 15, true);


--
-- Name: workspace_schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workspace_schedules_id_seq', 6, true);


--
-- Name: workspaces_fylecredential_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workspaces_fylecredential_id_seq', 3, true);


--
-- Name: workspaces_sageintacctcredential_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workspaces_sageintacctcredential_id_seq', 3, true);


--
-- Name: workspaces_workspace_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workspaces_workspace_id_seq', 3, true);


--
-- Name: workspaces_workspace_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workspaces_workspace_user_id_seq', 4, true);


--
-- Name: workspaces_workspacegeneralsettings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workspaces_workspacegeneralsettings_id_seq', 3, true);


--
-- Name: ap_payment_lineitems ap_payment_lineitems_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payment_lineitems
    ADD CONSTRAINT ap_payment_lineitems_pkey PRIMARY KEY (id);


--
-- Name: ap_payments ap_payments_expense_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payments
    ADD CONSTRAINT ap_payments_expense_group_id_key UNIQUE (expense_group_id);


--
-- Name: ap_payments ap_payments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payments
    ADD CONSTRAINT ap_payments_pkey PRIMARY KEY (id);


--
-- Name: auth_cache auth_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_cache
    ADD CONSTRAINT auth_cache_pkey PRIMARY KEY (cache_key);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: category_mappings category_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_pkey PRIMARY KEY (id);


--
-- Name: cost_codes cost_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cost_codes
    ADD CONSTRAINT cost_codes_pkey PRIMARY KEY (id);


--
-- Name: cost_codes cost_codes_workspace_id_task_id_project_id_a6a0e72d_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cost_codes
    ADD CONSTRAINT cost_codes_workspace_id_task_id_project_id_a6a0e72d_uniq UNIQUE (workspace_id, task_id, project_id);


--
-- Name: cost_types cost_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cost_types
    ADD CONSTRAINT cost_types_pkey PRIMARY KEY (id);


--
-- Name: cost_types cost_types_record_number_workspace_id_a86dce01_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cost_types
    ADD CONSTRAINT cost_types_record_number_workspace_id_a86dce01_uniq UNIQUE (record_number, workspace_id);


--
-- Name: dependent_field_settings dependent_fields_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dependent_field_settings
    ADD CONSTRAINT dependent_fields_pkey PRIMARY KEY (id);


--
-- Name: dependent_field_settings dependent_fields_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dependent_field_settings
    ADD CONSTRAINT dependent_fields_workspace_id_key UNIQUE (workspace_id);


--
-- Name: destination_attributes destination_attributes_destination_id_attribute_d22ab1fe_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_attributes
    ADD CONSTRAINT destination_attributes_destination_id_attribute_d22ab1fe_uniq UNIQUE (destination_id, attribute_type, workspace_id, display_name);


--
-- Name: dimension_details dimension_details_attribute_type_display_n_3070e1bc_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dimension_details
    ADD CONSTRAINT dimension_details_attribute_type_display_n_3070e1bc_uniq UNIQUE (attribute_type, display_name, workspace_id, source_type);


--
-- Name: dimension_details dimension_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dimension_details
    ADD CONSTRAINT dimension_details_pkey PRIMARY KEY (id);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_q_ormq django_q_ormq_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_q_ormq
    ADD CONSTRAINT django_q_ormq_pkey PRIMARY KEY (id);


--
-- Name: django_q_schedule django_q_schedule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_q_schedule
    ADD CONSTRAINT django_q_schedule_pkey PRIMARY KEY (id);


--
-- Name: django_q_task django_q_task_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_q_task
    ADD CONSTRAINT django_q_task_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: employee_mappings employee_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings
    ADD CONSTRAINT employee_mappings_pkey PRIMARY KEY (id);


--
-- Name: employee_mappings employee_mappings_source_employee_id_dd9948ba_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings
    ADD CONSTRAINT employee_mappings_source_employee_id_dd9948ba_uniq UNIQUE (source_employee_id);


--
-- Name: errors errors_expense_attribute_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.errors
    ADD CONSTRAINT errors_expense_attribute_id_key UNIQUE (expense_attribute_id);


--
-- Name: errors errors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.errors
    ADD CONSTRAINT errors_pkey PRIMARY KEY (id);


--
-- Name: expense_attributes_deletion_cache expense_attributes_deletion_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_attributes_deletion_cache
    ADD CONSTRAINT expense_attributes_deletion_cache_pkey PRIMARY KEY (id);


--
-- Name: expense_attributes_deletion_cache expense_attributes_deletion_cache_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_attributes_deletion_cache
    ADD CONSTRAINT expense_attributes_deletion_cache_workspace_id_key UNIQUE (workspace_id);


--
-- Name: expense_attributes expense_attributes_value_attribute_type_wor_a06aa6b3_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_attributes
    ADD CONSTRAINT expense_attributes_value_attribute_type_wor_a06aa6b3_uniq UNIQUE (value, attribute_type, workspace_id);


--
-- Name: expense_fields expense_fields_attribute_type_workspace_id_22d6ab60_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_fields
    ADD CONSTRAINT expense_fields_attribute_type_workspace_id_22d6ab60_uniq UNIQUE (attribute_type, workspace_id);


--
-- Name: expense_fields expense_fields_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_fields
    ADD CONSTRAINT expense_fields_pkey PRIMARY KEY (id);


--
-- Name: expense_filters expense_filters_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_filters
    ADD CONSTRAINT expense_filters_pkey PRIMARY KEY (id);


--
-- Name: expense_group_settings expense_group_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_group_settings
    ADD CONSTRAINT expense_group_settings_pkey PRIMARY KEY (id);


--
-- Name: expense_group_settings expense_group_settings_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_group_settings
    ADD CONSTRAINT expense_group_settings_workspace_id_key UNIQUE (workspace_id);


--
-- Name: expense_groups_expenses expense_groups_expenses_expensegroup_id_expense__6a42b67c_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups_expenses
    ADD CONSTRAINT expense_groups_expenses_expensegroup_id_expense__6a42b67c_uniq UNIQUE (expensegroup_id, expense_id);


--
-- Name: failed_events failed_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.failed_events
    ADD CONSTRAINT failed_events_pkey PRIMARY KEY (id);


--
-- Name: feature_configs feature_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feature_configs
    ADD CONSTRAINT feature_configs_pkey PRIMARY KEY (id);


--
-- Name: feature_configs feature_configs_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feature_configs
    ADD CONSTRAINT feature_configs_workspace_id_key UNIQUE (workspace_id);


--
-- Name: destination_attributes fyle_accounting_mappings_destinationattribute_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_attributes
    ADD CONSTRAINT fyle_accounting_mappings_destinationattribute_pkey PRIMARY KEY (id);


--
-- Name: expense_attributes fyle_accounting_mappings_expenseattribute_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_attributes
    ADD CONSTRAINT fyle_accounting_mappings_expenseattribute_pkey PRIMARY KEY (id);


--
-- Name: mappings fyle_accounting_mappings_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mappings
    ADD CONSTRAINT fyle_accounting_mappings_mapping_pkey PRIMARY KEY (id);


--
-- Name: mapping_settings fyle_accounting_mappings_mappingsetting_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mapping_settings
    ADD CONSTRAINT fyle_accounting_mappings_mappingsetting_pkey PRIMARY KEY (id);


--
-- Name: mappings fyle_accounting_mappings_source_type_source_id_de_e40411c3_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mappings
    ADD CONSTRAINT fyle_accounting_mappings_source_type_source_id_de_e40411c3_uniq UNIQUE (source_type, source_id, destination_type, workspace_id);


--
-- Name: expenses fyle_expense_expense_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT fyle_expense_expense_id_key UNIQUE (expense_id);


--
-- Name: expenses fyle_expense_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT fyle_expense_pkey PRIMARY KEY (id);


--
-- Name: expense_groups_expenses fyle_expensegroup_expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups_expenses
    ADD CONSTRAINT fyle_expensegroup_expenses_pkey PRIMARY KEY (id);


--
-- Name: expense_groups fyle_expensegroup_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups
    ADD CONSTRAINT fyle_expensegroup_pkey PRIMARY KEY (id);


--
-- Name: auth_tokens fyle_rest_auth_authtokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_tokens
    ADD CONSTRAINT fyle_rest_auth_authtokens_pkey PRIMARY KEY (id);


--
-- Name: auth_tokens fyle_rest_auth_authtokens_user_id_3b4bd82e_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_tokens
    ADD CONSTRAINT fyle_rest_auth_authtokens_user_id_3b4bd82e_uniq UNIQUE (user_id);


--
-- Name: fyle_sync_timestamps fyle_sync_timestamps_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fyle_sync_timestamps
    ADD CONSTRAINT fyle_sync_timestamps_pkey PRIMARY KEY (id);


--
-- Name: general_mappings general_mappings_workspace_id_19666c5c_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.general_mappings
    ADD CONSTRAINT general_mappings_workspace_id_19666c5c_uniq UNIQUE (workspace_id);


--
-- Name: import_logs import_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.import_logs
    ADD CONSTRAINT import_logs_pkey PRIMARY KEY (id);


--
-- Name: import_logs import_logs_workspace_id_attribute_type_42f69b7b_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.import_logs
    ADD CONSTRAINT import_logs_workspace_id_attribute_type_42f69b7b_uniq UNIQUE (workspace_id, attribute_type);


--
-- Name: intacct_sync_timestamps intacct_sync_timestamps_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.intacct_sync_timestamps
    ADD CONSTRAINT intacct_sync_timestamps_pkey PRIMARY KEY (id);


--
-- Name: journal_entries journal_entries_expense_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entries
    ADD CONSTRAINT journal_entries_expense_group_id_key UNIQUE (expense_group_id);


--
-- Name: journal_entries journal_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entries
    ADD CONSTRAINT journal_entries_pkey PRIMARY KEY (id);


--
-- Name: journal_entry_lineitems journal_entry_lineitems_expense_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entry_lineitems
    ADD CONSTRAINT journal_entry_lineitems_expense_id_key UNIQUE (expense_id);


--
-- Name: journal_entry_lineitems journal_entry_lineitems_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entry_lineitems
    ADD CONSTRAINT journal_entry_lineitems_pkey PRIMARY KEY (id);


--
-- Name: last_export_details last_export_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.last_export_details
    ADD CONSTRAINT last_export_details_pkey PRIMARY KEY (id);


--
-- Name: last_export_details last_export_details_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.last_export_details
    ADD CONSTRAINT last_export_details_workspace_id_key UNIQUE (workspace_id);


--
-- Name: location_entity_mappings location_entity_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.location_entity_mappings
    ADD CONSTRAINT location_entity_mappings_pkey PRIMARY KEY (id);


--
-- Name: location_entity_mappings location_entity_mappings_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.location_entity_mappings
    ADD CONSTRAINT location_entity_mappings_workspace_id_key UNIQUE (workspace_id);


--
-- Name: mapping_settings mapping_settings_source_field_destination_cdc65270_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mapping_settings
    ADD CONSTRAINT mapping_settings_source_field_destination_cdc65270_uniq UNIQUE (source_field, destination_field, workspace_id);


--
-- Name: general_mappings mappings_generalmapping_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.general_mappings
    ADD CONSTRAINT mappings_generalmapping_pkey PRIMARY KEY (id);


--
-- Name: reimbursements reimbursements_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reimbursements
    ADD CONSTRAINT reimbursements_pkey PRIMARY KEY (id);


--
-- Name: reimbursements reimbursements_workspace_id_payment_number_4854354c_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reimbursements
    ADD CONSTRAINT reimbursements_workspace_id_payment_number_4854354c_uniq UNIQUE (workspace_id, payment_number);


--
-- Name: sage_intacct_attributes_count sage_intacct_attributes_count_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_attributes_count
    ADD CONSTRAINT sage_intacct_attributes_count_pkey PRIMARY KEY (id);


--
-- Name: sage_intacct_attributes_count sage_intacct_attributes_count_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_attributes_count
    ADD CONSTRAINT sage_intacct_attributes_count_workspace_id_key UNIQUE (workspace_id);


--
-- Name: bills sage_intacct_bill_expense_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bills
    ADD CONSTRAINT sage_intacct_bill_expense_group_id_key UNIQUE (expense_group_id);


--
-- Name: bills sage_intacct_bill_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bills
    ADD CONSTRAINT sage_intacct_bill_pkey PRIMARY KEY (id);


--
-- Name: bill_lineitems sage_intacct_billlineitem_expense_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bill_lineitems
    ADD CONSTRAINT sage_intacct_billlineitem_expense_id_key UNIQUE (expense_id);


--
-- Name: bill_lineitems sage_intacct_billlineitem_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bill_lineitems
    ADD CONSTRAINT sage_intacct_billlineitem_pkey PRIMARY KEY (id);


--
-- Name: charge_card_transactions sage_intacct_chargecardtransaction_expense_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transactions
    ADD CONSTRAINT sage_intacct_chargecardtransaction_expense_group_id_key UNIQUE (expense_group_id);


--
-- Name: charge_card_transactions sage_intacct_chargecardtransaction_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transactions
    ADD CONSTRAINT sage_intacct_chargecardtransaction_pkey PRIMARY KEY (id);


--
-- Name: charge_card_transaction_lineitems sage_intacct_chargecardtransactionlineitem_expense_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transaction_lineitems
    ADD CONSTRAINT sage_intacct_chargecardtransactionlineitem_expense_id_key UNIQUE (expense_id);


--
-- Name: charge_card_transaction_lineitems sage_intacct_chargecardtransactionlineitem_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transaction_lineitems
    ADD CONSTRAINT sage_intacct_chargecardtransactionlineitem_pkey PRIMARY KEY (id);


--
-- Name: expense_reports sage_intacct_expensereport_expense_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_reports
    ADD CONSTRAINT sage_intacct_expensereport_expense_group_id_key UNIQUE (expense_group_id);


--
-- Name: expense_reports sage_intacct_expensereport_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_reports
    ADD CONSTRAINT sage_intacct_expensereport_pkey PRIMARY KEY (id);


--
-- Name: expense_report_lineitems sage_intacct_expensereportlineitem_expense_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_report_lineitems
    ADD CONSTRAINT sage_intacct_expensereportlineitem_expense_id_key UNIQUE (expense_id);


--
-- Name: expense_report_lineitems sage_intacct_expensereportlineitem_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_report_lineitems
    ADD CONSTRAINT sage_intacct_expensereportlineitem_pkey PRIMARY KEY (id);


--
-- Name: sage_intacct_reimbursement_lineitems sage_intacct_reimbursement_lineitems_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursement_lineitems
    ADD CONSTRAINT sage_intacct_reimbursement_lineitems_pkey PRIMARY KEY (id);


--
-- Name: sage_intacct_reimbursements sage_intacct_reimbursements_expense_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursements
    ADD CONSTRAINT sage_intacct_reimbursements_expense_group_id_key UNIQUE (expense_group_id);


--
-- Name: sage_intacct_reimbursements sage_intacct_reimbursements_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursements
    ADD CONSTRAINT sage_intacct_reimbursements_pkey PRIMARY KEY (id);


--
-- Name: task_logs task_logs_expense_group_id_f19c75f9_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_expense_group_id_f19c75f9_uniq UNIQUE (expense_group_id);


--
-- Name: task_logs tasks_tasklog_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT tasks_tasklog_pkey PRIMARY KEY (id);


--
-- Name: update_logs update_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.update_logs
    ADD CONSTRAINT update_logs_pkey PRIMARY KEY (id);


--
-- Name: users users_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_user_pkey PRIMARY KEY (id);


--
-- Name: users users_user_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_user_user_id_key UNIQUE (user_id);


--
-- Name: workspace_schedules workspace_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspace_schedules
    ADD CONSTRAINT workspace_schedules_pkey PRIMARY KEY (id);


--
-- Name: workspace_schedules workspace_schedules_schedule_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspace_schedules
    ADD CONSTRAINT workspace_schedules_schedule_id_key UNIQUE (schedule_id);


--
-- Name: workspace_schedules workspace_schedules_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspace_schedules
    ADD CONSTRAINT workspace_schedules_workspace_id_key UNIQUE (workspace_id);


--
-- Name: fyle_credentials workspaces_fylecredential_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fyle_credentials
    ADD CONSTRAINT workspaces_fylecredential_pkey PRIMARY KEY (id);


--
-- Name: fyle_credentials workspaces_fylecredential_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fyle_credentials
    ADD CONSTRAINT workspaces_fylecredential_workspace_id_key UNIQUE (workspace_id);


--
-- Name: sage_intacct_credentials workspaces_sageintacctcredential_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_credentials
    ADD CONSTRAINT workspaces_sageintacctcredential_pkey PRIMARY KEY (id);


--
-- Name: sage_intacct_credentials workspaces_sageintacctcredential_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_credentials
    ADD CONSTRAINT workspaces_sageintacctcredential_workspace_id_key UNIQUE (workspace_id);


--
-- Name: workspaces_user workspaces_user_workspace_id_user_id_aee37428_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces_user
    ADD CONSTRAINT workspaces_user_workspace_id_user_id_aee37428_uniq UNIQUE (workspace_id, user_id);


--
-- Name: workspaces workspaces_workspace_fyle_org_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces
    ADD CONSTRAINT workspaces_workspace_fyle_org_id_key UNIQUE (fyle_org_id);


--
-- Name: workspaces workspaces_workspace_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces
    ADD CONSTRAINT workspaces_workspace_pkey PRIMARY KEY (id);


--
-- Name: workspaces_user workspaces_workspace_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces_user
    ADD CONSTRAINT workspaces_workspace_user_pkey PRIMARY KEY (id);


--
-- Name: configurations workspaces_workspacegeneralsettings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configurations
    ADD CONSTRAINT workspaces_workspacegeneralsettings_pkey PRIMARY KEY (id);


--
-- Name: configurations workspaces_workspacegeneralsettings_workspace_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configurations
    ADD CONSTRAINT workspaces_workspacegeneralsettings_workspace_id_key UNIQUE (workspace_id);


--
-- Name: ap_payment_lineitems_ap_payment_id_c7f4cfd8; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ap_payment_lineitems_ap_payment_id_c7f4cfd8 ON public.ap_payment_lineitems USING btree (ap_payment_id);


--
-- Name: auth_cache_expires; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_cache_expires ON public.auth_cache USING btree (expires);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: bill_lineitems_bill_id_8d61e31f; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX bill_lineitems_bill_id_8d61e31f ON public.bill_lineitems USING btree (bill_id);


--
-- Name: category_mappings_destination_account_id_ebc44c1c; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX category_mappings_destination_account_id_ebc44c1c ON public.category_mappings USING btree (destination_account_id);


--
-- Name: category_mappings_destination_expense_head_id_0ed87fbd; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX category_mappings_destination_expense_head_id_0ed87fbd ON public.category_mappings USING btree (destination_expense_head_id);


--
-- Name: category_mappings_source_category_id_46f19d95; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX category_mappings_source_category_id_46f19d95 ON public.category_mappings USING btree (source_category_id);


--
-- Name: category_mappings_workspace_id_222ea301; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX category_mappings_workspace_id_222ea301 ON public.category_mappings USING btree (workspace_id);


--
-- Name: charge_card_transaction_li_charge_card_transaction_id_508bf6be; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX charge_card_transaction_li_charge_card_transaction_id_508bf6be ON public.charge_card_transaction_lineitems USING btree (charge_card_transaction_id);


--
-- Name: cost_codes_workspa_1590e9_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX cost_codes_workspa_1590e9_idx ON public.cost_codes USING btree (workspace_id, task_id);


--
-- Name: cost_codes_workspa_5ac5ff_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX cost_codes_workspa_5ac5ff_idx ON public.cost_codes USING btree (workspace_id, project_id);


--
-- Name: cost_codes_workspace_id_1efc24ee; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX cost_codes_workspace_id_1efc24ee ON public.cost_codes USING btree (workspace_id);


--
-- Name: cost_types_project_04e2f5_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX cost_types_project_04e2f5_idx ON public.cost_types USING btree (project_id);


--
-- Name: cost_types_task_id_085813_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX cost_types_task_id_085813_idx ON public.cost_types USING btree (task_id);


--
-- Name: cost_types_task_na_17ecec_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX cost_types_task_na_17ecec_idx ON public.cost_types USING btree (task_name);


--
-- Name: cost_types_workspace_id_c71fcac0; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX cost_types_workspace_id_c71fcac0 ON public.cost_types USING btree (workspace_id);


--
-- Name: dimension_details_workspace_id_c09745f3; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX dimension_details_workspace_id_c09745f3 ON public.dimension_details USING btree (workspace_id);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_q_task_id_32882367_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_q_task_id_32882367_like ON public.django_q_task USING btree (id varchar_pattern_ops);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: employee_mappings_destination_card_account_id_f030b899; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX employee_mappings_destination_card_account_id_f030b899 ON public.employee_mappings USING btree (destination_card_account_id);


--
-- Name: employee_mappings_destination_employee_id_b6764819; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX employee_mappings_destination_employee_id_b6764819 ON public.employee_mappings USING btree (destination_employee_id);


--
-- Name: employee_mappings_destination_vendor_id_c4bd73df; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX employee_mappings_destination_vendor_id_c4bd73df ON public.employee_mappings USING btree (destination_vendor_id);


--
-- Name: employee_mappings_workspace_id_4a25f8c9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX employee_mappings_workspace_id_4a25f8c9 ON public.employee_mappings USING btree (workspace_id);


--
-- Name: errors_expense_group_id_86fafc8b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX errors_expense_group_id_86fafc8b ON public.errors USING btree (expense_group_id);


--
-- Name: errors_workspace_id_a33dd61b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX errors_workspace_id_a33dd61b ON public.errors USING btree (workspace_id);


--
-- Name: expense_fields_workspace_id_b60af18c; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expense_fields_workspace_id_b60af18c ON public.expense_fields USING btree (workspace_id);


--
-- Name: expense_filters_workspace_id_0ecd4914; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expense_filters_workspace_id_0ecd4914 ON public.expense_filters USING btree (workspace_id);


--
-- Name: expense_groups_expenses_expense_id_af963907; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expense_groups_expenses_expense_id_af963907 ON public.expense_groups_expenses USING btree (expense_id);


--
-- Name: expense_groups_expenses_expensegroup_id_c5b379a2; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expense_groups_expenses_expensegroup_id_c5b379a2 ON public.expense_groups_expenses USING btree (expensegroup_id);


--
-- Name: expense_groups_workspace_id_21fcb4ac; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expense_groups_workspace_id_21fcb4ac ON public.expense_groups USING btree (workspace_id);


--
-- Name: expense_report_lineitems_expense_report_id_4c7e2508; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expense_report_lineitems_expense_report_id_4c7e2508 ON public.expense_report_lineitems USING btree (expense_report_id);


--
-- Name: expenses_account_ff34f0_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expenses_account_ff34f0_idx ON public.expenses USING btree (accounting_export_summary, workspace_id);


--
-- Name: expenses_expense_id_0e3511ea_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expenses_expense_id_0e3511ea_like ON public.expenses USING btree (expense_id varchar_pattern_ops);


--
-- Name: expenses_fund_so_386913_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expenses_fund_so_386913_idx ON public.expenses USING btree (fund_source, workspace_id);


--
-- Name: expenses_workspa_ad984e_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expenses_workspa_ad984e_idx ON public.expenses USING btree (workspace_id, report_id);


--
-- Name: expenses_workspace_id_72fb819f; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX expenses_workspace_id_72fb819f ON public.expenses USING btree (workspace_id);


--
-- Name: fyle_accounting_mappings_d_workspace_id_a6a3ab6a; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fyle_accounting_mappings_d_workspace_id_a6a3ab6a ON public.destination_attributes USING btree (workspace_id);


--
-- Name: fyle_accounting_mappings_expenseattribute_workspace_id_4364b6d7; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fyle_accounting_mappings_expenseattribute_workspace_id_4364b6d7 ON public.expense_attributes USING btree (workspace_id);


--
-- Name: fyle_accounting_mappings_mapping_destination_id_79497f6e; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fyle_accounting_mappings_mapping_destination_id_79497f6e ON public.mappings USING btree (destination_id);


--
-- Name: fyle_accounting_mappings_mapping_source_id_7d692c36; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fyle_accounting_mappings_mapping_source_id_7d692c36 ON public.mappings USING btree (source_id);


--
-- Name: fyle_accounting_mappings_mapping_workspace_id_10d6edd3; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fyle_accounting_mappings_mapping_workspace_id_10d6edd3 ON public.mappings USING btree (workspace_id);


--
-- Name: fyle_accounting_mappings_mappingsetting_workspace_id_c123c088; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fyle_accounting_mappings_mappingsetting_workspace_id_c123c088 ON public.mapping_settings USING btree (workspace_id);


--
-- Name: fyle_sync_timestamps_workspace_id_1afd9a31; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fyle_sync_timestamps_workspace_id_1afd9a31 ON public.fyle_sync_timestamps USING btree (workspace_id);


--
-- Name: import_logs_workspace_id_e5acf2ff; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX import_logs_workspace_id_e5acf2ff ON public.import_logs USING btree (workspace_id);


--
-- Name: intacct_sync_timestamps_workspace_id_980f86e0; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX intacct_sync_timestamps_workspace_id_980f86e0 ON public.intacct_sync_timestamps USING btree (workspace_id);


--
-- Name: journal_entry_lineitems_journal_entry_id_382a8abe; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX journal_entry_lineitems_journal_entry_id_382a8abe ON public.journal_entry_lineitems USING btree (journal_entry_id);


--
-- Name: mapping_settings_expense_field_id_e9afc6c2; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX mapping_settings_expense_field_id_e9afc6c2 ON public.mapping_settings USING btree (expense_field_id);


--
-- Name: reimbursements_workspace_id_084805e4; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX reimbursements_workspace_id_084805e4 ON public.reimbursements USING btree (workspace_id);


--
-- Name: sage_intacct_attributes_count_updated_at_5f7b9275; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX sage_intacct_attributes_count_updated_at_5f7b9275 ON public.sage_intacct_attributes_count USING btree (updated_at);


--
-- Name: sage_intacct_reimbursement_sage_intacct_reimbursement_96b8e4d9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX sage_intacct_reimbursement_sage_intacct_reimbursement_96b8e4d9 ON public.sage_intacct_reimbursement_lineitems USING btree (sage_intacct_reimbursement_id);


--
-- Name: task_logs_ap_payment_id_51b8a8b4; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_ap_payment_id_51b8a8b4 ON public.task_logs USING btree (ap_payment_id);


--
-- Name: task_logs_bill_id_f4fc5218; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_bill_id_f4fc5218 ON public.task_logs USING btree (bill_id);


--
-- Name: task_logs_charge_card_transaction_id_0a86b771; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_charge_card_transaction_id_0a86b771 ON public.task_logs USING btree (charge_card_transaction_id);


--
-- Name: task_logs_expense_report_id_0eda6a81; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_expense_report_id_0eda6a81 ON public.task_logs USING btree (expense_report_id);


--
-- Name: task_logs_journal_entry_id_8c699a31; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_journal_entry_id_8c699a31 ON public.task_logs USING btree (journal_entry_id);


--
-- Name: task_logs_sage_intacct_reimbursement_id_d336c210; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_sage_intacct_reimbursement_id_d336c210 ON public.task_logs USING btree (sage_intacct_reimbursement_id);


--
-- Name: task_logs_workspace_id_d6109445; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX task_logs_workspace_id_d6109445 ON public.task_logs USING btree (workspace_id);


--
-- Name: users_user_user_id_4120b7b9_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX users_user_user_id_4120b7b9_like ON public.users USING btree (user_id varchar_pattern_ops);


--
-- Name: workspaces_fyle_org_id_a77e6782_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX workspaces_fyle_org_id_a77e6782_like ON public.workspaces USING btree (fyle_org_id varchar_pattern_ops);


--
-- Name: workspaces_user_user_id_4253baf7; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX workspaces_user_user_id_4253baf7 ON public.workspaces_user USING btree (user_id);


--
-- Name: workspaces_user_workspace_id_be6c5867; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX workspaces_user_workspace_id_be6c5867 ON public.workspaces_user USING btree (workspace_id);


--
-- Name: prod_active_workspaces_view _RETURN; Type: RULE; Schema: public; Owner: postgres
--

CREATE OR REPLACE VIEW public.prod_active_workspaces_view AS
 SELECT w.id,
    w.name,
    w.fyle_org_id,
    w.last_synced_at,
    w.created_at,
    w.updated_at,
    w.destination_synced_at,
    w.source_synced_at,
    w.cluster_domain,
    w.ccc_last_synced_at,
    w.onboarding_state,
    w.app_version,
    array_agg(u.email) AS user_emails
   FROM ((public.workspaces w
     JOIN public.workspaces_user wu ON ((wu.workspace_id = w.id)))
     JOIN public.users u ON ((u.id = wu.user_id)))
  WHERE (((u.email)::text !~~* '%fyle%'::text) AND (w.id IN ( SELECT DISTINCT task_logs.workspace_id
           FROM public.task_logs
          WHERE (((task_logs.status)::text = 'COMPLETE'::text) AND ((task_logs.type)::text <> 'FETCHING_EXPENSES'::text) AND (task_logs.updated_at > (now() - '3 mons'::interval))))))
  GROUP BY w.id;


--
-- Name: prod_workspaces_view _RETURN; Type: RULE; Schema: public; Owner: postgres
--

CREATE OR REPLACE VIEW public.prod_workspaces_view AS
 SELECT w.id,
    w.name,
    w.fyle_org_id,
    w.last_synced_at,
    w.created_at,
    w.updated_at,
    w.destination_synced_at,
    w.source_synced_at,
    w.cluster_domain,
    w.ccc_last_synced_at,
    w.onboarding_state,
    w.app_version,
    array_agg(u.email) AS user_emails
   FROM ((public.workspaces w
     JOIN public.workspaces_user wu ON ((wu.workspace_id = w.id)))
     JOIN public.users u ON ((u.id = wu.user_id)))
  WHERE ((u.email)::text !~~* '%fyle%'::text)
  GROUP BY w.id;


--
-- Name: configurations monitor_updates; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER monitor_updates AFTER UPDATE ON public.configurations FOR EACH ROW EXECUTE FUNCTION public.log_update_event();


--
-- Name: expense_group_settings monitor_updates; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER monitor_updates AFTER UPDATE ON public.expense_group_settings FOR EACH ROW EXECUTE FUNCTION public.log_update_event();


--
-- Name: general_mappings monitor_updates; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER monitor_updates AFTER UPDATE ON public.general_mappings FOR EACH ROW EXECUTE FUNCTION public.log_update_event();


--
-- Name: mapping_settings monitor_updates; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER monitor_updates AFTER UPDATE ON public.mapping_settings FOR EACH ROW EXECUTE FUNCTION public.log_update_event();


--
-- Name: ap_payment_lineitems ap_payment_lineitems_ap_payment_id_c7f4cfd8_fk_ap_payments_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payment_lineitems
    ADD CONSTRAINT ap_payment_lineitems_ap_payment_id_c7f4cfd8_fk_ap_payments_id FOREIGN KEY (ap_payment_id) REFERENCES public.ap_payments(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: ap_payments ap_payments_expense_group_id_9e5dd4dc_fk_expense_groups_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ap_payments
    ADD CONSTRAINT ap_payments_expense_group_id_9e5dd4dc_fk_expense_groups_id FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: bill_lineitems bill_lineitems_bill_id_8d61e31f_fk_bills_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bill_lineitems
    ADD CONSTRAINT bill_lineitems_bill_id_8d61e31f_fk_bills_id FOREIGN KEY (bill_id) REFERENCES public.bills(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: bill_lineitems bill_lineitems_expense_id_fc7ff7c3_fk_expenses_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bill_lineitems
    ADD CONSTRAINT bill_lineitems_expense_id_fc7ff7c3_fk_expenses_id FOREIGN KEY (expense_id) REFERENCES public.expenses(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: bills bills_expense_group_id_245e4cc1_fk_expense_groups_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bills
    ADD CONSTRAINT bills_expense_group_id_245e4cc1_fk_expense_groups_id FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: category_mappings category_mappings_destination_account__ebc44c1c_fk_destinati; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_destination_account__ebc44c1c_fk_destinati FOREIGN KEY (destination_account_id) REFERENCES public.destination_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: category_mappings category_mappings_destination_expense__0ed87fbd_fk_destinati; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_destination_expense__0ed87fbd_fk_destinati FOREIGN KEY (destination_expense_head_id) REFERENCES public.destination_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: category_mappings category_mappings_source_category_id_46f19d95_fk_expense_a; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_source_category_id_46f19d95_fk_expense_a FOREIGN KEY (source_category_id) REFERENCES public.expense_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: category_mappings category_mappings_workspace_id_222ea301_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category_mappings
    ADD CONSTRAINT category_mappings_workspace_id_222ea301_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: charge_card_transaction_lineitems charge_card_transact_charge_card_transact_508bf6be_fk_charge_ca; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transaction_lineitems
    ADD CONSTRAINT charge_card_transact_charge_card_transact_508bf6be_fk_charge_ca FOREIGN KEY (charge_card_transaction_id) REFERENCES public.charge_card_transactions(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: charge_card_transactions charge_card_transact_expense_group_id_a00fb88a_fk_expense_g; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transactions
    ADD CONSTRAINT charge_card_transact_expense_group_id_a00fb88a_fk_expense_g FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: charge_card_transaction_lineitems charge_card_transact_expense_id_d662cef7_fk_expenses_; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.charge_card_transaction_lineitems
    ADD CONSTRAINT charge_card_transact_expense_id_d662cef7_fk_expenses_ FOREIGN KEY (expense_id) REFERENCES public.expenses(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cost_codes cost_codes_workspace_id_1efc24ee_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cost_codes
    ADD CONSTRAINT cost_codes_workspace_id_1efc24ee_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cost_types cost_types_workspace_id_c71fcac0_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cost_types
    ADD CONSTRAINT cost_types_workspace_id_c71fcac0_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dependent_field_settings dependent_field_settings_workspace_id_dd0a1e77_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dependent_field_settings
    ADD CONSTRAINT dependent_field_settings_workspace_id_dd0a1e77_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dimension_details dimension_details_workspace_id_c09745f3_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dimension_details
    ADD CONSTRAINT dimension_details_workspace_id_c09745f3_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_users_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_users_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: employee_mappings employee_mappings_destination_card_acc_f030b899_fk_destinati; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings
    ADD CONSTRAINT employee_mappings_destination_card_acc_f030b899_fk_destinati FOREIGN KEY (destination_card_account_id) REFERENCES public.destination_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: employee_mappings employee_mappings_destination_employee_b6764819_fk_destinati; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings
    ADD CONSTRAINT employee_mappings_destination_employee_b6764819_fk_destinati FOREIGN KEY (destination_employee_id) REFERENCES public.destination_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: employee_mappings employee_mappings_destination_vendor_i_c4bd73df_fk_destinati; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings
    ADD CONSTRAINT employee_mappings_destination_vendor_i_c4bd73df_fk_destinati FOREIGN KEY (destination_vendor_id) REFERENCES public.destination_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: employee_mappings employee_mappings_source_employee_id_dd9948ba_fk_expense_a; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings
    ADD CONSTRAINT employee_mappings_source_employee_id_dd9948ba_fk_expense_a FOREIGN KEY (source_employee_id) REFERENCES public.expense_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: employee_mappings employee_mappings_workspace_id_4a25f8c9_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_mappings
    ADD CONSTRAINT employee_mappings_workspace_id_4a25f8c9_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: errors errors_expense_attribute_id_23be4f13_fk_expense_attributes_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.errors
    ADD CONSTRAINT errors_expense_attribute_id_23be4f13_fk_expense_attributes_id FOREIGN KEY (expense_attribute_id) REFERENCES public.expense_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: errors errors_expense_group_id_86fafc8b_fk_expense_groups_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.errors
    ADD CONSTRAINT errors_expense_group_id_86fafc8b_fk_expense_groups_id FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: errors errors_workspace_id_a33dd61b_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.errors
    ADD CONSTRAINT errors_workspace_id_a33dd61b_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_attributes_deletion_cache expense_attributes_d_workspace_id_e00d2384_fk_workspace; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_attributes_deletion_cache
    ADD CONSTRAINT expense_attributes_d_workspace_id_e00d2384_fk_workspace FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_fields expense_fields_workspace_id_b60af18c_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_fields
    ADD CONSTRAINT expense_fields_workspace_id_b60af18c_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_filters expense_filters_workspace_id_0ecd4914_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_filters
    ADD CONSTRAINT expense_filters_workspace_id_0ecd4914_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_group_settings expense_group_settings_workspace_id_4c110bbe_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_group_settings
    ADD CONSTRAINT expense_group_settings_workspace_id_4c110bbe_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_groups_expenses expense_groups_expen_expensegroup_id_c5b379a2_fk_expense_g; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups_expenses
    ADD CONSTRAINT expense_groups_expen_expensegroup_id_c5b379a2_fk_expense_g FOREIGN KEY (expensegroup_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_groups_expenses expense_groups_expenses_expense_id_af963907_fk_expenses_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups_expenses
    ADD CONSTRAINT expense_groups_expenses_expense_id_af963907_fk_expenses_id FOREIGN KEY (expense_id) REFERENCES public.expenses(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_groups expense_groups_workspace_id_21fcb4ac_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_groups
    ADD CONSTRAINT expense_groups_workspace_id_21fcb4ac_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_report_lineitems expense_report_linei_expense_report_id_4c7e2508_fk_expense_r; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_report_lineitems
    ADD CONSTRAINT expense_report_linei_expense_report_id_4c7e2508_fk_expense_r FOREIGN KEY (expense_report_id) REFERENCES public.expense_reports(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_report_lineitems expense_report_lineitems_expense_id_847445bc_fk_expenses_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_report_lineitems
    ADD CONSTRAINT expense_report_lineitems_expense_id_847445bc_fk_expenses_id FOREIGN KEY (expense_id) REFERENCES public.expenses(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_reports expense_reports_expense_group_id_3f864e9a_fk_expense_groups_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_reports
    ADD CONSTRAINT expense_reports_expense_group_id_3f864e9a_fk_expense_groups_id FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expenses expenses_workspace_id_72fb819f_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_workspace_id_72fb819f_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: feature_configs feature_configs_workspace_id_2161bfdc_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feature_configs
    ADD CONSTRAINT feature_configs_workspace_id_2161bfdc_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: mappings fyle_accounting_mapp_workspace_id_10d6edd3_fk_workspace; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mappings
    ADD CONSTRAINT fyle_accounting_mapp_workspace_id_10d6edd3_fk_workspace FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: expense_attributes fyle_accounting_mapp_workspace_id_4364b6d7_fk_workspace; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expense_attributes
    ADD CONSTRAINT fyle_accounting_mapp_workspace_id_4364b6d7_fk_workspace FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: destination_attributes fyle_accounting_mapp_workspace_id_a6a3ab6a_fk_workspace; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.destination_attributes
    ADD CONSTRAINT fyle_accounting_mapp_workspace_id_a6a3ab6a_fk_workspace FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: fyle_credentials fyle_credentials_workspace_id_52f7febf_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fyle_credentials
    ADD CONSTRAINT fyle_credentials_workspace_id_52f7febf_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_tokens fyle_rest_auth_authtokens_user_id_3b4bd82e_fk_users_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_tokens
    ADD CONSTRAINT fyle_rest_auth_authtokens_user_id_3b4bd82e_fk_users_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: fyle_sync_timestamps fyle_sync_timestamps_workspace_id_1afd9a31_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fyle_sync_timestamps
    ADD CONSTRAINT fyle_sync_timestamps_workspace_id_1afd9a31_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: general_mappings general_mappings_workspace_id_19666c5c_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.general_mappings
    ADD CONSTRAINT general_mappings_workspace_id_19666c5c_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: import_logs import_logs_workspace_id_e5acf2ff_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.import_logs
    ADD CONSTRAINT import_logs_workspace_id_e5acf2ff_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: intacct_sync_timestamps intacct_sync_timestamps_workspace_id_980f86e0_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.intacct_sync_timestamps
    ADD CONSTRAINT intacct_sync_timestamps_workspace_id_980f86e0_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: journal_entries journal_entries_expense_group_id_6cdaa98b_fk_expense_groups_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entries
    ADD CONSTRAINT journal_entries_expense_group_id_6cdaa98b_fk_expense_groups_id FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: journal_entry_lineitems journal_entry_lineit_journal_entry_id_382a8abe_fk_journal_e; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entry_lineitems
    ADD CONSTRAINT journal_entry_lineit_journal_entry_id_382a8abe_fk_journal_e FOREIGN KEY (journal_entry_id) REFERENCES public.journal_entries(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: journal_entry_lineitems journal_entry_lineitems_expense_id_5a5ca4ff_fk_expenses_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_entry_lineitems
    ADD CONSTRAINT journal_entry_lineitems_expense_id_5a5ca4ff_fk_expenses_id FOREIGN KEY (expense_id) REFERENCES public.expenses(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: last_export_details last_export_details_workspace_id_0af72f0e_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.last_export_details
    ADD CONSTRAINT last_export_details_workspace_id_0af72f0e_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: location_entity_mappings location_entity_mappings_workspace_id_efc692f9_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.location_entity_mappings
    ADD CONSTRAINT location_entity_mappings_workspace_id_efc692f9_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: mapping_settings mapping_settings_expense_field_id_e9afc6c2_fk_expense_fields_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mapping_settings
    ADD CONSTRAINT mapping_settings_expense_field_id_e9afc6c2_fk_expense_fields_id FOREIGN KEY (expense_field_id) REFERENCES public.expense_fields(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: mapping_settings mapping_settings_workspace_id_590f14f3_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mapping_settings
    ADD CONSTRAINT mapping_settings_workspace_id_590f14f3_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: mappings mappings_destination_id_0c60b033_fk_destination_attributes_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mappings
    ADD CONSTRAINT mappings_destination_id_0c60b033_fk_destination_attributes_id FOREIGN KEY (destination_id) REFERENCES public.destination_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: mappings mappings_source_id_fd4f378f_fk_expense_attributes_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mappings
    ADD CONSTRAINT mappings_source_id_fd4f378f_fk_expense_attributes_id FOREIGN KEY (source_id) REFERENCES public.expense_attributes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: reimbursements reimbursements_workspace_id_084805e4_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reimbursements
    ADD CONSTRAINT reimbursements_workspace_id_084805e4_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sage_intacct_attributes_count sage_intacct_attribu_workspace_id_014830bb_fk_workspace; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_attributes_count
    ADD CONSTRAINT sage_intacct_attribu_workspace_id_014830bb_fk_workspace FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sage_intacct_credentials sage_intacct_credentials_workspace_id_119b2476_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_credentials
    ADD CONSTRAINT sage_intacct_credentials_workspace_id_119b2476_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sage_intacct_reimbursements sage_intacct_reimbur_expense_group_id_c6b34ea2_fk_expense_g; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursements
    ADD CONSTRAINT sage_intacct_reimbur_expense_group_id_c6b34ea2_fk_expense_g FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sage_intacct_reimbursement_lineitems sage_intacct_reimbur_sage_intacct_reimbur_96b8e4d9_fk_sage_inta; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sage_intacct_reimbursement_lineitems
    ADD CONSTRAINT sage_intacct_reimbur_sage_intacct_reimbur_96b8e4d9_fk_sage_inta FOREIGN KEY (sage_intacct_reimbursement_id) REFERENCES public.sage_intacct_reimbursements(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_ap_payment_id_51b8a8b4_fk_ap_payments_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_ap_payment_id_51b8a8b4_fk_ap_payments_id FOREIGN KEY (ap_payment_id) REFERENCES public.ap_payments(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_bill_id_f4fc5218_fk_bills_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_bill_id_f4fc5218_fk_bills_id FOREIGN KEY (bill_id) REFERENCES public.bills(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_charge_card_transact_0a86b771_fk_charge_ca; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_charge_card_transact_0a86b771_fk_charge_ca FOREIGN KEY (charge_card_transaction_id) REFERENCES public.charge_card_transactions(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_expense_group_id_f19c75f9_fk_expense_groups_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_expense_group_id_f19c75f9_fk_expense_groups_id FOREIGN KEY (expense_group_id) REFERENCES public.expense_groups(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_expense_report_id_0eda6a81_fk_expense_reports_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_expense_report_id_0eda6a81_fk_expense_reports_id FOREIGN KEY (expense_report_id) REFERENCES public.expense_reports(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_journal_entry_id_8c699a31_fk_journal_entries_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_journal_entry_id_8c699a31_fk_journal_entries_id FOREIGN KEY (journal_entry_id) REFERENCES public.journal_entries(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_sage_intacct_reimbur_d336c210_fk_sage_inta; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_sage_intacct_reimbur_d336c210_fk_sage_inta FOREIGN KEY (sage_intacct_reimbursement_id) REFERENCES public.sage_intacct_reimbursements(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: task_logs task_logs_workspace_id_d6109445_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_logs
    ADD CONSTRAINT task_logs_workspace_id_d6109445_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: workspace_schedules workspace_schedules_schedule_id_70b3d838_fk_django_q_; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspace_schedules
    ADD CONSTRAINT workspace_schedules_schedule_id_70b3d838_fk_django_q_ FOREIGN KEY (schedule_id) REFERENCES public.django_q_schedule(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: workspace_schedules workspace_schedules_workspace_id_50ec990f_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspace_schedules
    ADD CONSTRAINT workspace_schedules_workspace_id_50ec990f_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: workspaces_user workspaces_user_user_id_4253baf7_fk_users_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces_user
    ADD CONSTRAINT workspaces_user_user_id_4253baf7_fk_users_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: workspaces_user workspaces_user_workspace_id_be6c5867_fk_workspaces_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workspaces_user
    ADD CONSTRAINT workspaces_user_workspace_id_be6c5867_fk_workspaces_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--


