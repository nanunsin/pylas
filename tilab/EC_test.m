clear all
close all
clc

% 2017. 01.

las = load('S1C1_K_N_A_M01_L2-2_1500.txt');
data = load('gcp_9.txt');

fn = sprintf('result_test.txt'); 
fid_ip = fopen(fn,'w');

% setting
count_gcp = size(data,1) - 2;
count_las = size(las,1); %15000000

shift_xyz = [0 0 0];
 
 for i = 1:(count_gcp+1)     
     delta_x = data(i+1,5) - data(i+1,2);
     delta_y = data(i+1,6) - data(i+1,3);
     delta_z = data(i+1,7) - data(i+1,4);
     delta_xyz = [delta_x delta_y delta_z];
     num = (data(i+1,1) - data(i,1));
     
     if i == count_gcp+1
         delta_xyz = [0 0 0];
     end 
     
     for k = 1 : num
         row = k + data(i,1);
         before_xyz = [las(row,1) las(row,2) las(row,3)];
         after_xyz = before_xyz + shift_xyz + ((delta_xyz-shift_xyz)/num) * k;

         fprintf(fid_ip,'%.2f  %.2f  %.2f %d \n', after_xyz(1), after_xyz(2), after_xyz(3), las(row,4));
     end
     shift_xyz = delta_xyz;
     
 end
 
 fclose(fid_ip);

 
%     
%     time_Scan = las(i,8) / 1000000; 
%     time_INS = (rem(POSLV(k,1), 86400) - 17);
%     time_diff = time_Scan - time_INS;
%     
%     if time_diff < 0
%         XYZI = georeferencing(las(i,1:3), las(i,4), scan_Att, scan_Lever, Bo_XYZ, Bo_angle, POSLV(k,3:5), POSLV(k,9:11));
%         fprintf(fid_ip,'%.3f  %.3f  %.3f  %d \n', XYZI(1),XYZI(2),XYZI(3),XYZI(4));
%        
%     elseif time_diff == 0
%         XYZI = georeferencing(las(i,1:3), las(i,4), scan_Att, scan_Lever, Bo_XYZ, Bo_angle, POSLV(k,3:5), POSLV(k,9:11));
%         fprintf(fid_ip,'%.3f  %.3f  %.3f  %d \n', XYZI(1),XYZI(2),XYZI(3),XYZI(4));
%         
%     else
%         after_diff = abs((time_Scan - (rem(POSLV(k+1,1), 86400)-17)));
%         now_diff = abs(time_diff);
%         
%         if after_diff >= now_diff
%             XYZI = georeferencing(las(i,1:3), las(i,4), scan_Att, scan_Lever, Bo_XYZ, Bo_angle, POSLV(k,3:5), POSLV(k,9:11));
%             fprintf(fid_ip,'%.3f  %.3f  %.3f  %d \n', XYZI(1),XYZI(2),XYZI(3),XYZI(4));
%         else
%             XYZI = georeferencing(las(i,1:3), las(i,4), scan_Att, scan_Lever, Bo_XYZ, Bo_angle, POSLV(k+1,3:5), POSLV(k+1,9:11));
%             fprintf(fid_ip,'%.3f  %.3f  %.3f  %d \n', XYZI(1),XYZI(2),XYZI(3),XYZI(4));
%             k = k + 1;
%         end
%         
%     end
%         
%  end
 

