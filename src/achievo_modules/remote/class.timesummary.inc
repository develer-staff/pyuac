<?php
/*
 * Copyright 2007 Develer S.r.l. (http://www.develer.com/)
 * All rights reserved.
 *
 * $Id: $
 * Author: Matteo Bertini <naufraghi@develer.com>
 */

useattrib("atkdateattribute");

class timesummary extends atkNode
{
    function timesummary()
    {
        $this->atkNode("timesummary");
    }
    
    function get_timesummary()
    {
        global $g_user;
        $userid = $g_user["id"];

        $db = &atkGetDb();

        /* Accetta una data in ingresso oppure imposta l'intervallo all'ultimo mese appena concluso*/
        $last_month_start  = mktime(0, 0, 0, date("m")-1, 1, date("Y"));
        $last_month_end = mktime(0, 0, 0, date("m"), 0, date("Y"));
        $date_start = $this->m_postvars['date_start'];
        $date_end = $this->m_postvars['date_end'];
        if ($date_start == "")
            $date_start = date("Y-m-d", $last_month_start);
        else
            $date_start = sprintf("%04d",$date_start["year"])."-".sprintf("%02d",$date_start["month"])."-".sprintf("%02d",$date_start["day"]);
        if ($date_end == "")
            $date_end = date("Y-m-d", $last_month_end);
        else
            $date_end = sprintf("%04d",$date_end["year"])."-".sprintf("%02d",$date_end["month"])."-".sprintf("%02d",$date_end["day"]);

        /* Accetta un testo con due colonne:
            username euro/ora
        */
        $euro_ora_text = $this->m_postvars['euro_ora_text'];
        $euro_ora_array = array();
        foreach (explode("\n", $euro_ora_text) as $line)
        {
            $line = explode(" ", $line);
            $euro_ora_array[$line[0]] = $line[1];
        }
        atkdebug("euro_ora_array: ".var_export($euro_ora_array, 1));

        $select = "
                SELECT
                    person.userid,
                    project.name AS prj,
                    sum(hours.time)/60.0 as ore
                FROM hours
                    JOIN person ON hours.userid = person.id
                    JOIN phase ON hours.phaseid = phase.id
                    JOIN activity ON hours.activityid = activity.id
                    JOIN project ON phase.projectid = project.id";
        $filter = "
                WHERE
                    activitydate >= '$date_start' AND
                    activitydate <= '$date_end'";
        if (!$this->allowed("any_user")) $filter.= " AND hours.userid ='$userid' ";
        $groupby = "
                GROUP BY userid, prj
                ORDER BY userid, prj";

        $sql = $select . $filter . $groupby;

        return array("date_start" => $date_start,
                     "date_end" => $date_end,
                     "euro_ora_array" => $euro_ora_array,
                     "rows" => $db->getRows($sql));
    }
    
    function action_search()
    {
        atkdebug("timesummary Action search");
        
        $results = $this->get_timesummary();
        echo make_xml("timesummary", "$date_start<=D<=$date_end", $results['rows'], $bodykey="remark");
        exit;
    }
    
    function action_report()
    {
        $ui = &$this->getUi();
        $page = &$this->getPage();
        $this->addStyle("style.css");
        $content = '<form action="dispatch.php" method="get" name="entryform">';
        $content .= session_form();
        
        $results = $this->get_timesummary();
        $title = "Timereport: ".$results["date_start"]." - ".$results["date_end"];

        $startdateatt = new atkDateAttribute("date_start","F d Y","d F Y", 0, $results["date_start"], AF_OBLIGATORY);
        $enddateatt = new atkDateAttribute("date_end","F d Y","d F Y", 0, $results["date_end"], AF_OBLIGATORY);

        $content .= "Da ".$startdateatt->edit()." a ".$enddateatt->edit();

        // Tabella ore lavorate per progetto
        $content .= "<table border='1'>\n";
        $content .= "<tr><th>User Id</th><th>Progetto</th><th>Ore</th><th>Euro</th></tr>\n";
        $ore_progetto = array();
        $ore_persona = array();
        foreach ($results['rows'] as $key => $r)
        {
            if (!array_key_exists($r['prj'], $ore_progetto)) $ore_progetto[$r['prj']] = 0.0;
            if (!array_key_exists($r['userid'], $ore_persona)) $ore_persona[$r['userid']] = 0.0;
            $ore_progetto[$r['prj']] += $r['ore'];
            $ore_persona[$r['userid']] += $r['ore'];

            atkdebug("Euro ora loop: ".var_export($r, 1)." incr ore prj:".$ore_progetto[$r['prj']].", user:".$ore_persona[$r['userid']]);

            if (array_key_exists($r['userid'], $results['euro_ora_array']))
            {
                $r['euro'] = $r['ore'] * $results['euro_ora_array'][$r['userid']];
            }
            else
            {
                $r['euro'] = "Manca euro/h";
            }
            $content .= "<tr><td>".$r['userid']."</td><td>".$r['prj']."</td><td>".round($r['ore'], 2)."</td><td>".$r['euro']."</td></tr>\n";
        }
        $content .= "</table>";
        
        // Tabella ore per progetto / ore per persona
        $content .= "<table border='1'><tr><th>Totale ore progetto</th><th>Totale ore persona</th></tr>";
        $content .= "<tr><td>";
        ksort($ore_progetto); //Ordina per chiave, le persone sono già ordinate
        foreach ($ore_progetto as $key => $r)
        {
            $content .= "<b>$key</b>: $r<br/>";
        }
        $content .= "</td><td>";
        foreach ($ore_persona as $key => $r)
        {
            $content .= "<b>$key</b>: $r<br/>";
        }
        $content .= "</td></tr></table>";

        $content .= "<table><tr><td>Inserire: nome_utente euro/h</td></tr>\n";
        $content .= "<tr><td><textarea rows='20' cols='80' name='euro_ora_text'>".$this->m_postvars['euro_ora_text']."</textarea>";
        $content .= "</td></tr></table>\n";

        $content .= '<input type="submit" value="'.atktext("refresh").'"></form>';
        $content .= '<input type="hidden" name="atknodetype" value="'.$this->atkNodeType().'">';
        $content .= '<input type="hidden" name="atkaction" value="report">';
        $page->addContent($ui->renderBox(array("title"=>$title,"content"=>$content)));
    }
}
?>
