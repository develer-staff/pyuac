<?php
/*
 * Copyright 2007 Develer S.r.l. (http://www.develer.com/)
 * All rights reserved.
 *
 * $Id: $
 * Author: Matteo Bertini <naufraghi@develer.com>
 */

include_once (moduleDir("remote")."class.timereg.inc");

function isTime($time)
{
    list ($h, $m) = split (":", $time);

    if (!$h)
        return false;

    if (!ctype_digit($h))
        return false;

    if ($m && !ctype_digit($m))
        return false;

    if ($h < 0 || $h >= 24)
        return false;

    if ($m < 0 || $m >= 60)
        return false;

    return true;
}

function smartLike($field, $s)
{
    return "LOWER($field) LIKE LOWER('%$s%')";
}

function tokenize($s)
{
    // Trim extra spaces
    $s = preg_replace("/\s+/", " ", $s);
    $s = trim($s);
    $s = addslashes($s);

    return split(" ", $s);
}

class query extends atkNode
{
    function query()
    {
        $this->atkNode("query");
        $this->setSecurityAlias("remote.timereg");
    }

    function action_search()
    {
        atkdebug("Action search");
        /*
         * The input string must be in the following form:
         * project [phase [activity [hours [comment]]]]
         *
         * This is an example of input string and its meaning:
         *
         * String  = the big project planning development 10:15 initial structure
         *           --------------- -------- ----------- ----- -----------------
         * Meaning =     project      phase    activity   hours      comment
         *
         */

        /*
         * TODO: In realtà "search" non ha interesse a conoscere ore e commento.
         * Quello interessa solo alla funzione di inserimento.
         * Quindi quei due campi andrebbero gestiti lato client ed inviati a
         * timereg una volta controllati.
        */
        global $g_user;

        $db = &atkGetDb();

        $string = $this->m_postvars['input'];

        $tokens = tokenize($string);

        // Fill $guesses with all the alternatives
        for ($prj_len = 1; $prj_len <= sizeof($tokens); ++$prj_len)
        {
            for ($phase_len = 0; $phase_len <= sizeof($tokens) - $prj_len; ++$phase_len)
            {
                for ($activity_len = 0; $activity_len <= sizeof($tokens) - ($prj_len + $phase_len); ++$activity_len)
                {
                    $prj = join(" ", array_slice($tokens, 0, $prj_len));
                    $phase = join(" ", array_slice($tokens, $prj_len, $phase_len));
                    $activity = join(" ", array_slice($tokens, $prj_len + $phase_len, $activity_len));
                    $hours = join(" ", array_slice($tokens, $prj_len + $phase_len + $activity_len, 1));
                    $remark = join(" ", array_slice($tokens, $prj_len + $phase_len + $activity_len + 1));

                    // Filter out some invalid record to reduce the sql query
                    if ($hours and !isTime($hours))
                    {
                        #echo "$hours not a time\n";
                        continue;
                    }

                    $guesses[] = array (
                        "in_prj"   => $prj,
                        "in_pha"   => $phase,
                        "in_act"   => $activity,
                        "in_hmtime"   => $hours,
                        "in_remark"   => $remark);
                }
            }
        }

        foreach ($guesses as $k => $g)
        {
            $sql .= "
                SELECT
                    $k AS k,
                    project.name AS prj,
                    phase.name AS pha,
                    activity.name AS act,
                    project.id AS projectid,
                    phase.id AS phaseid,
                    activity.id AS activityid
                FROM
                    project
                    JOIN phase ON project.id = phase.projectid
                    JOIN phase_activity ON phase.id = phase_activity.phaseid
                    JOIN activity ON phase_activity.activityid = activity.id
                    JOIN project_person ON project.id = project_person.projectid
                WHERE
                    project.status = 'active' AND
                    project_person.personid = " . $g_user["id"] . " AND
                    (
                    (" . smartLike("project.name", $guesses[$k]["in_prj"]) . ") AND
                    (" . smartLike("phase.name", $guesses[$k]["in_pha"]) . ") AND
                    (" . smartLike("activity.name", $guesses[$k]["in_act"]) . ")
                    )";

            if ($k != sizeof($guesses) - 1)
                $sql .= " UNION ";
        }

        $results = $db->getRows($sql);

        // Merge $result and $guesses
        foreach ($results as $i => $r)
        {
            $k = $results[$i]["k"];
            $results[$i] = array_merge($results[$i], $guesses[$k]);
        }

        echo make_xml("query", "OK", $results, $bodykey="in_remark");

        exit;
    }
}
?>
