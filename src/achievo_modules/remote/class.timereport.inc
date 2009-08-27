<?php
/*
 * Copyright 2007 Develer S.r.l. (http://www.develer.com/)
 * All rights reserved.
 *
 * $Id: $
 * Author: Matteo Bertini <naufraghi@develer.com>
 */

include_once (moduleDir("remote")."class.timereg.inc");

class timereport extends atkNode
{
    function timereport()
    {
        $this->atkNode("timereport");
        $this->setSecurityAlias("remote.timereg");
    }

    function action_search()
    {
        atkdebug("timereport Action search");
        global $g_user;

        $db = &atkGetDb();
        $date = $this->m_postvars['date'];
        // faccio un controllo per far passare solo le date
        // nel formato YYYY[-][M]M[-][D]D
        if (!is_array($date))
            $date = array($date);
        $date = array_filter($date, is_valid_date);
        $date = str_replace("-","", $date);
        $datelist = implode("','", $date);

        $sql = "
                SELECT
                    hours.id,
                    hours.time,
                    hours.remark,
                    hours.activitydate AS activitydate,
                    project.name AS prj,
                    activity.name AS act,
                    phase.name AS pha
                FROM hours
                    JOIN phase ON hours.phaseid = phase.id
                    JOIN activity ON hours.activityid = activity.id
                    JOIN project ON phase.projectid = project.id
                WHERE
                    userid = " . $g_user["id"] . " AND
                    activitydate IN ('$datelist','0')
                    ORDER BY activitydate DESC
        ";
        $results = $db->getRows($sql);

        echo make_xml("timereport", "OK", $results, $bodykey="remark");
        exit;
    }
}
?>
