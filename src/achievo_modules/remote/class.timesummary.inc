<?php
/*
 * Copyright 2007 Develer S.r.l. (http://www.develer.com/)
 * All rights reserved.
 *
 * $Id: $
 * Author: Matteo Bertini <naufraghi@develer.com>
 */

include_once (moduleDir("remote")."class.timereg.inc");

class timesummary extends atkNode
{
    function timesummary()
    {
        $this->atkNode("timesummary");
        $this->setSecurityAlias("remote.timereg");
    }

    function action_search()
    {
        atkdebug("timesummary Action search");
        global $g_user;

        $db = &atkGetDb();
        $date_start = $this->m_postvars['date_start'];
        $date_end = $this->m_postvars['date_end'];
        $last_month_start  = mktime(0, 0, 0, date("m")-1, 1,  date("Y"));
        $last_month_end = mktime(0, 0, 0, date("m"), 0,  date("Y"));
        if ($date_start == "") $date_start = date("Y-m-d", $last_month_start);
        if ($date_end == "") $date_end = date("Y-m-d", $last_month_end);
        // faccio un controllo per far passare solo le date
        // nel formato YYYY[-][M]M[-][D]D
        $date_start = str_replace("-","", $date_start);
        $date_end = str_replace("-","", $date_end);

        $sql = "
                SELECT
                    person.userid,
                    project.name AS prj,
                    sum(hours.time)/60.0 as ore
                FROM hours
                    JOIN person ON hours.userid = person.id
                    JOIN phase ON hours.phaseid = phase.id
                    JOIN activity ON hours.activityid = activity.id
                    JOIN project ON phase.projectid = project.id
                WHERE
                    activitydate >= '$date_start' AND
                    activitydate <= '$date_end'
                GROUP BY userid, prj
        ";
        $results = $db->getRows($sql);

        echo make_xml("timesummary", "$date_start<=D<=$date_end", $results, $bodykey="remark");
        exit;
    }
}
?>
